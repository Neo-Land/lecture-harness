"""Checks that every generated claim is grounded in the slides it cites.

Three layers, cheapest first:
  1. citation  - claim cites slides that exist (deterministic)
  2. exact_fact - numbers / quoted terms / `code` in the claim appear in cited slides (deterministic)
  3. judge     - an LLM decides whether the cited slides support the paraphrase (probabilistic)
"""

from __future__ import annotations

import re
from typing import Protocol

from .models import Claim, Deck, Issue, Summary, VerificationReport

NUMBER = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)*%?")
QUOTED = re.compile(r"[\"“]([^\"”]{2,60})[\"”]")
CODE = re.compile(r"`([^`]{1,60})`")


class Judge(Protocol):
    def supports(self, claim: str, evidence: str) -> tuple[bool, str]: ...


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace(",", "")).lower()


def extract_facts(text: str) -> list[str]:
    """Things that must appear verbatim in the source: numbers, "quoted" phrases, `code`."""
    facts = [m.group(0).rstrip("%") for m in NUMBER.finditer(text)]
    facts += QUOTED.findall(text) + CODE.findall(text)
    return facts


def evidence_for(claim: Claim, deck: Deck) -> str:
    return "\n".join(s.text for n in claim.slides if (s := deck.slide(n)))


def check_claim(claim: Claim, deck: Deck, judge: Judge | None = None) -> list[Issue]:
    missing = [n for n in claim.slides if deck.slide(n) is None]
    if missing:
        return [Issue(claim=claim.text, check="citation", detail=f"cites nonexistent slide(s) {missing}")]

    evidence = _norm(evidence_for(claim, deck))
    absent = [f for f in extract_facts(claim.text) if _norm(f) not in evidence]
    if absent:
        return [
            Issue(
                claim=claim.text, check="exact_fact", detail=f"not found on slides {claim.slides}: {absent}"
            )
        ]

    if judge:
        ok, why = judge.supports(claim.text, evidence_for(claim, deck))
        if not ok:
            return [Issue(claim=claim.text, check="judge", detail=why)]
    return []


def verify_claims(claims: list[Claim], deck: Deck, judge: Judge | None = None) -> VerificationReport:
    issues = [i for c in claims for i in check_claim(c, deck, judge)]
    bad = {i.claim for i in issues}
    return VerificationReport(
        passed=not issues,
        issues=issues,
        claims_total=len(claims),
        claims_supported=sum(c.text not in bad for c in claims),
    )


def verify_summary(summary: Summary, deck: Deck, judge: Judge | None = None) -> VerificationReport:
    report = verify_claims(summary.abstract, deck, judge)
    for v in summary.visuals:  # visuals must cite real slides too
        bad = [n for n in v.slides if deck.slide(n) is None]
        if bad:
            report.issues.append(
                Issue(
                    claim=f"[visual] {v.title}", check="citation", detail=f"cites nonexistent slide(s) {bad}"
                )
            )
            report.passed = False
    return report
