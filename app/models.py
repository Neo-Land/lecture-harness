"""Core data shapes shared by the parser, harness, verifier and API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Slide(BaseModel):
    number: int  # 1-based, matches what students see
    text: str
    needs_ocr: bool = False  # no extractable text, e.g. a scanned page
    has_image: bool = False  # a rendered PNG exists for this slide


class Deck(BaseModel):
    id: str  # stable id (LMS file id or content hash)
    course: str
    title: str
    slides: list[Slide]

    def slide(self, n: int) -> Slide | None:
        return next((s for s in self.slides if s.number == n), None)


class Claim(BaseModel):
    text: str
    slides: list[int] = Field(min_length=1)  # every claim must cite >= 1 slide


class VisualSpec(BaseModel):
    """Structured visual the frontend renders. The model never draws pictures."""

    kind: Literal["concept_map", "table", "timeline", "key_terms"]
    title: str
    # concept_map: {"nodes": [...], "edges": [[a, b, label], ...]}
    # table: {"columns": [...], "rows": [[...], ...]}
    # timeline: {"events": [[label, detail], ...]}
    # key_terms: {"terms": [[term, definition], ...]}
    data: dict
    slides: list[int] = Field(min_length=1)


class Summary(BaseModel):
    abstract: list[Claim]
    visuals: list[VisualSpec] = []


class Issue(BaseModel):
    claim: str
    check: Literal["citation", "exact_fact", "judge"]
    detail: str


class VerificationReport(BaseModel):
    passed: bool
    issues: list[Issue] = []
    claims_total: int = 0
    claims_supported: int = 0


class Answer(BaseModel):
    """Reply to a UI question. Same grounding rules as summaries."""

    claims: list[Claim]
    insufficient_evidence: bool = False
