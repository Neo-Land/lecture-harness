"""Model access. The harness depends only on the `LLM` protocol, so tests can swap in a fake."""

from __future__ import annotations

import json
from typing import Protocol

from .config import settings
from .models import Answer, Claim, Deck, Issue, Slide, Summary
from .retrieval import tokenize


class LLM(Protocol):
    def summarize(self, deck: Deck, feedback: list[Issue]) -> Summary: ...
    def answer(self, question: str, slides: list[tuple[str, Slide]], feedback: list[Issue]) -> Answer: ...


SUMMARY_RULES = """You summarize lecture slides for a student.
Rules:
- Every claim cites the slide numbers it comes from. Use only those slides.
- Copy numbers, formulas and technical terms exactly as written on the slide.
- Wrap code identifiers in backticks only if they appear on the slide.
- Prefer 4-8 claims.
- Add 1-3 visuals (concept_map, table, timeline, key_terms) only when the slides support them.
- If revising, fix or drop every claim listed under FEEDBACK."""

ANSWER_RULES = """Answer the student's question using ONLY the slides provided.
Every claim cites slides as numbers from the provided list. If the slides don't answer it,
set insufficient_evidence=true and return no claims. Never use outside knowledge."""


def _format_slides(slides: list[tuple[str, Slide]]) -> str:
    return "\n\n".join(f"[slide {s.number} | {deck}]\n{s.text}" for deck, s in slides if s.text)


def _format_feedback(feedback: list[Issue]) -> str:
    if not feedback:
        return ""
    lines = "\n".join(f"- {i.claim!r}: {i.detail}" for i in feedback)
    return f"\n\nFEEDBACK (previous attempt failed verification):\n{lines}"


class ClaudeLLM:
    """Uses forced tool calls so output is always valid JSON matching our pydantic models."""

    def __init__(self, model: str | None = None):
        import anthropic  # imported lazily so tests don't need a key

        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = model or settings.model

    def _call(self, system: str, user: str, schema: dict, tool: str) -> dict:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system=system,
            tools=[{"name": tool, "description": "Submit the result.", "input_schema": schema}],
            tool_choice={"type": "tool", "name": tool},
            messages=[{"role": "user", "content": user}],
        )
        return next(b.input for b in resp.content if b.type == "tool_use")

    def summarize(self, deck: Deck, feedback: list[Issue]) -> Summary:
        slides = _format_slides([(deck.title, s) for s in deck.slides])
        data = self._call(
            SUMMARY_RULES, slides + _format_feedback(feedback), Summary.model_json_schema(), "submit_summary"
        )
        return Summary.model_validate(data)

    def answer(self, question: str, slides: list[tuple[str, Slide]], feedback: list[Issue]) -> Answer:
        user = f"{_format_slides(slides)}\n\nQUESTION: {question}{_format_feedback(feedback)}"
        data = self._call(ANSWER_RULES, user, Answer.model_json_schema(), "submit_answer")
        return Answer.model_validate(data)


class ClaudeJudge:
    """LLM-as-judge for paraphrased claims. Use a cheaper model than the writer."""

    def __init__(self, model: str | None = None):
        import anthropic

        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = model or settings.judge_model

    def supports(self, claim: str, evidence: str) -> tuple[bool, str]:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            system="Decide if EVIDENCE fully supports CLAIM. Reply JSON only: "
            '{"supported": true|false, "reason": "..."}',
            messages=[{"role": "user", "content": f"EVIDENCE:\n{evidence}\n\nCLAIM:\n{claim}"}],
        )
        try:
            out = json.loads(resp.content[0].text)
            return bool(out["supported"]), out.get("reason", "")
        except (json.JSONDecodeError, KeyError, IndexError):
            return False, "judge returned unparseable output"


class ExtractiveLLM:
    """Offline stand-in that quotes slides, for running the app with no API key. Not AI: it never
    paraphrases, so its output says nothing about how the real model or the verifier perform."""

    def summarize(self, deck: Deck, feedback: list[Issue]) -> Summary:
        slides = [s for s in deck.slides if s.text][:8]
        return Summary(abstract=[Claim(text=_longest_line(s.text), slides=[s.number]) for s in slides])

    def answer(self, question: str, slides: list[tuple[str, Slide]], feedback: list[Issue]) -> Answer:
        wanted = set(tokenize(question))
        claims = []
        for _, slide in slides[:3]:
            matching = [ln for ln in slide.text.splitlines() if wanted & set(tokenize(ln))]
            if matching:
                claims.append(Claim(text=_longest_line("\n".join(matching)), slides=[slide.number]))
        return Answer(claims=claims, insufficient_evidence=not claims)


def _longest_line(text: str) -> str:
    return max(text.splitlines(), key=len)


def make_llm(cfg) -> tuple[LLM, object | None]:
    """The model and judge for these settings. Offline mode has no judge."""
    if cfg.offline:
        return ExtractiveLLM(), None
    return ClaudeLLM(), ClaudeJudge() if cfg.use_judge else None
