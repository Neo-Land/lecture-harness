# 0002 — Start with FastAPI, SQLite, and BM25

- **Status:** accepted
- **Date:** 2026-10-30

## Context
The backend serves one student's course slides. It needs an HTTP API for the frontend, storage for
decks and summaries, and search across a course's slides for grounded answers. The accuracy work is
the point of the project, so the surrounding infrastructure should be small and need no services.

## Options considered
1. FastAPI + SQLite + hand-written BM25: no servers to run, no embedding costs, deterministic tests.
2. FastAPI + Postgres + vector database: scales further, but adds services and per-slide embedding
   costs before there is any measurement showing keyword search falls short.
3. A RAG framework: less code up front, but it hides the retrieval and verification steps this
   project needs to control and measure.

## Decision
Option 1. FastAPI generates the OpenAPI schema the Phase 4 typed client is built from. SQLite is one
local file, which fits private course data. BM25 suits slides, whose exact terms (function names,
acronyms) are what students search for, and it runs offline in tests.

## Consequences
- Keyword search misses synonyms: a question worded differently from the slides can find nothing and
  return `insufficient_evidence`. That fails safe, and Phase 3 evals can measure how often it happens.
- BM25 is recomputed over every slide per query. That is fine for one student's courses and is the
  first thing to change if a course grows very large.
- SQLite limits the public demo to a single API instance, which suits a read-only demo.
