# Architecture

## Flow
```
            ┌──────────── deterministic code ────────────┐   ┌─ model ─┐
LMS/upload ─► parsing.py ─► store.py ─► harness.py ─────────► llm.py
                                         │      ▲               │
                                         ▼      │ feedback      ▼
                                      verifier.py ◄──────── Summary / Answer (JSON)
                                         │
                                         ▼
                                  store.py ─► api.py ─► web/ (Phase 4)
```

## Modules
| Module | Responsibility | Deterministic? |
|---|---|---|
| `models.py` | Shared pydantic types (`Slide`, `Deck`, `Claim`, `VisualSpec`, `Summary`, `Answer`, reports) | yes |
| `parsing.py` | PDF/PPTX → numbered slides (text, tables, speaker notes) | yes |
| `verifier.py` | Citation, exact-fact, and judge checks per claim | layers 1–2 yes, 3 no |
| `llm.py` | Claude calls with forced tool use; `ClaudeJudge` | no |
| `harness.py` | Generate → verify → revise loop; answers over retrieved slides | yes (orchestration) |
| `retrieval.py` | BM25 keyword search over a course's slides | yes |
| `store.py` | SQLite: decks, summaries, processed LMS file versions | yes |
| `pipeline.py` | Sync new/changed LMS files and ingest them | yes |
| `lms/canvas.py` | Canvas REST client (token auth, pagination, download) | yes |
| `api.py` | FastAPI endpoints for the frontend | yes |

## Key invariants
1. Every `Claim` cites at least one slide (enforced by the model schema).
2. A claim is shown only if it passes the verifier; after `max_revisions`, failing claims are dropped.
3. Answers cite renumbered context slides that are mapped back to real `(deck, slide)` pairs, so
   the model can only cite slides it was shown.
4. Visuals are checked for valid slide citations only; the facts inside `VisualSpec.data` are not
   verified yet (known gap, tracked in Phase 1).
5. LMS files are processed once per version (`source_version` = Canvas `updated_at`).

## Endpoints
See `README.md` → Endpoints. Interactive docs at `/docs` when the server runs.
