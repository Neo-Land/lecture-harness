# 0001 — Verify every claim before showing it

- **Status:** accepted
- **Date:** 2026-10-30

## Context
LLM summaries of lecture slides can invent numbers, cite the wrong slide, or overgeneralize.
For study material, a confident wrong claim is worse than a missing one.

## Options considered
1. Trust the model, add a disclaimer — simple, but errors reach the student.
2. LLM-only self-check — catches paraphrase errors, but is probabilistic and misses exact-value slips.
3. Layered verifier: deterministic citation + exact-fact checks, then an LLM judge, with bounded revisions.

## Decision
Option 3. The model must return structured claims with slide citations. Deterministic checks run
first (cheap, reliable); the judge handles paraphrase. Failed claims are fed back for up to
`max_revisions` attempts and then dropped.

## Consequences
- Summaries may be shorter than the model would produce, which is acceptable.
- Exact-fact matching needs normalization work (unicode, units). Tracked in Phase 1.
- Verifier quality must be measured (Phase 3 planted-error set).
