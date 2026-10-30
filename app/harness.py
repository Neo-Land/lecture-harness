"""The harness loop: generate -> verify -> feed failures back -> revise (bounded).

The model only does judgment work (summarizing, answering). Everything deterministic
(fetching, parsing, citation checks, storage) happens in plain code around it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .llm import LLM
from .models import Answer, Claim, Deck, Slide, Summary, VerificationReport
from .retrieval import search
from .verifier import Judge, verify_claims, verify_summary

log = logging.getLogger("harness")


@dataclass
class RunResult:
    output: Summary | Answer
    report: VerificationReport
    attempts: int
    trace: list[dict] = field(default_factory=list)  # every attempt, for debugging + evals


def _drop_failed(claims: list[Claim], report: VerificationReport) -> list[Claim]:
    bad = {i.claim for i in report.issues}
    return [c for c in claims if c.text not in bad]


def summarize_deck(deck: Deck, llm: LLM, judge: Judge | None = None, max_revisions: int = 2) -> RunResult:
    feedback, trace = [], []
    for attempt in range(1, max_revisions + 2):
        summary = llm.summarize(deck, feedback)
        report = verify_summary(summary, deck, judge)
        trace.append({"attempt": attempt, "report": report.model_dump()})
        log.info(
            "deck=%s attempt=%d supported=%d/%d",
            deck.id,
            attempt,
            report.claims_supported,
            report.claims_total,
        )
        if report.passed:
            return RunResult(summary, report, attempt, trace)
        feedback = report.issues

    # Out of retries: never ship an unverified claim. Keep only what passed.
    summary.abstract = _drop_failed(summary.abstract, report)
    bad = {i.claim for i in report.issues}
    summary.visuals = [v for v in summary.visuals if f"[visual] {v.title}" not in bad]
    return RunResult(summary, report, attempt, trace)


@dataclass
class Citation:
    deck_id: str
    deck_title: str
    slide: int


def answer_question(
    question: str, decks: list[Deck], llm: LLM, judge: Judge | None = None, max_revisions: int = 1, k: int = 6
) -> tuple[RunResult, dict[int, Citation]]:
    """Retrieve top-k slides, renumber them 1..k as a temporary 'context deck' the model cites,
    verify against that deck, then map citations back to real (deck, slide) pairs."""
    hits = search(decks, question, k=k)
    citations = {i + 1: Citation(d.id, d.title, s.number) for i, (d, s, _) in enumerate(hits)}
    context = Deck(
        id="context",
        course="",
        title="context",
        slides=[Slide(number=i + 1, text=s.text) for i, (_, s, _) in enumerate(hits)],
    )
    labeled = [(d.title, Slide(number=i + 1, text=s.text)) for i, (d, s, _) in enumerate(hits)]

    if not hits:
        empty = Answer(claims=[], insufficient_evidence=True)
        return RunResult(empty, VerificationReport(passed=True), 0), {}

    feedback, trace = [], []
    for attempt in range(1, max_revisions + 2):
        ans = llm.answer(question, labeled, feedback)
        report = verify_claims(ans.claims, context, judge)
        trace.append({"attempt": attempt, "report": report.model_dump()})
        if report.passed:
            return RunResult(ans, report, attempt, trace), citations
        feedback = report.issues

    ans.claims = _drop_failed(ans.claims, report)
    ans.insufficient_evidence = ans.insufficient_evidence or not ans.claims
    return RunResult(ans, report, attempt, trace), citations
