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
| `llm.py` | Claude calls with forced tool use; `ClaudeJudge`; `ExtractiveLLM` for offline mode | no (offline mode yes) |
| `harness.py` | Generate → verify → revise loop; answers over retrieved slides | yes (orchestration) |
| `retrieval.py` | BM25 keyword search over a course's slides | yes |
| `store.py` | SQLite: decks, summaries, traces of every attempt, processed LMS file versions | yes |
| `pipeline.py` | Sync new/changed LMS files and ingest them | yes |
| `lms/canvas.py` | Canvas REST client (token auth, pagination, download) | yes |
| `api.py` | FastAPI endpoints for the frontend | yes |
| `__main__.py` | CLI: `ingest`, `ask` | yes |
| `config.py` | Settings; `validate_settings` fails fast at startup | yes |
| `logs.py` | JSON-lines log formatter | yes |

## Key invariants
1. Every `Claim` cites at least one slide (enforced by the model schema).
2. A claim is shown only if it passes the verifier; after `max_revisions`, failing claims are dropped.
3. Answers cite renumbered context slides that are mapped back to real `(deck, slide)` pairs, so
   the model can only cite slides it was shown.
4. Visuals go through the same checks as claims and are dropped if they still fail. Numbers pool
   across a visual's cells, so only the judge can catch a right number in the wrong cell.
5. LMS files are processed once per version (`source_version` = Canvas `updated_at`).

## Slide images
Ingest renders each slide to `data/images/<deck>/<n>.png` as a best-effort step (see ADR 0003). Every
summary records the model id and prompt version that produced it.

## Scanned slides
A slide with no extractable text is flagged `needs_ocr`. Citing it fails verification, and a fully
scanned deck skips the model call entirely and stores an empty summary.

## How facts are compared
Slide text and claims are normalized first (unicode, superscripts, LaTeX, dashes, thousands separators,
spacing). Numbers then compare by value and sign, so `4` never matches inside `0.42`, and `3.5` equals
`3.50`. A unit must match unless the slide shows the number bare, since a table header may hold it.
Quoted terms and `code` must match whole words.

## Endpoints
See `README.md` → Endpoints. Interactive docs at `/docs` when the server runs.
