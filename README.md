# Lecture Harness

[![CI](https://github.com/Neo-Land/lecture-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/Neo-Land/lecture-harness/actions/workflows/ci.yml)

An agent harness that pulls new lecture slides from your LMS, writes an abstract and
structured visuals, and **verifies every claim against the slides it cites** before
showing it to you. Ask questions per course and get answers with clickable slide citations.

```
LMS sync ─► parse slides ─► model writes JSON summary ─► verifier ─► store ─► API / UI
                                   ▲                         │
                                   └── failed claims fed back (max N revisions)
```

## How accuracy is enforced

| Check | How | Catches |
|---|---|---|
| Citation | every claim cites slides that exist | invented slide references |
| Exact fact | numbers, `"quoted terms"`, and `` `code` `` must appear on the **cited** slide | wrong numbers, renamed functions, facts from the wrong slide |
| Judge | a second, cheaper model checks paraphrases against slide text | unsupported generalizations |

If a claim still fails after the revision budget, it's **dropped**, never shown.
Questions with no supporting slides return `insufficient_evidence: true` instead of a guess.

## Command line

```bash
python -m app ingest lecture7.pdf --course "CS 2"
python -m app ask "What is merge sort's worst case?" --course "CS 2"
```

Add `--offline` (or set `HARNESS_OFFLINE=true`) to run with no API key. Offline mode is not AI: it only
quotes lines from the slides. Logs go to stderr as JSON lines, so stdout stays clean.

Real-model check, which costs money: see [`docs/RESULTS.md`](docs/RESULTS.md).

## Layout

```
app/
  models.py     pydantic shapes (Slide, Deck, Claim, VisualSpec, Summary, Answer)
  parsing.py    PDF / PPTX -> numbered slides (incl. speaker notes and tables)
  verifier.py   citation, exact-fact, and judge checks
  llm.py        Claude via forced tool calls (always-valid JSON) + LLM judge
  harness.py    generate -> verify -> revise loop; question answering over retrieved slides
  retrieval.py  BM25 keyword search across a course's slides
  store.py      SQLite: decks, summaries, which LMS file versions are already processed
  pipeline.py   sync new/changed files and run them through the harness
  lms/canvas.py Canvas REST client (personal access token)
  api.py        FastAPI endpoints for the frontend
  __main__.py   command line (ingest, ask)
  logs.py       JSON-lines logging
  config.py     settings and startup validation
tests/          runs offline with a scripted fake model
```

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env            # add your Anthropic key; Canvas is optional
pytest --cov=app                # no API key needed
ruff check . && ruff format --check .
set -a; source .env; set +a
uvicorn app.api:app --reload    # http://localhost:8000/docs
```

| Endpoint | Purpose |
|---|---|
| `GET /health` | liveness check |
| `POST /upload` (form: `course`, `file`) | add a PDF/PPTX manually |
| `POST /sync` | pull new/changed files from Canvas |
| `GET /courses`, `GET /courses/{course}/decks` | browse |
| `GET /decks/{id}` | slides + verified summary + verification report |
| `GET /decks/{id}/slides/{n}` | one slide (for citation links) |
| `GET /decks/{id}/slides/{n}/image` | the slide as a PNG (PPTX needs LibreOffice installed) |
| `POST /ask` `{course, question}` | grounded answer with sources |

## Project docs

- [`CLAUDE.md`](CLAUDE.md) — rules for Claude Code in this repo
- [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md) — phases, tasks, current status
- [`docs/SETUP_ACCESS.md`](docs/SETUP_ACCESS.md) — setup and what access to grant
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) · [`docs/decisions/`](docs/decisions/) · [`CHANGELOG.md`](CHANGELOG.md)

## Next steps

- [ ] Golden eval set (5-10 decks with hand-written key points) -> report grounding %, coverage, hallucinations caught
- [ ] Next.js frontend: course sidebar, lecture page (abstract + visuals + slides), ask box
- [ ] Cache summaries by file hash; scheduled sync

> Course slides are usually your professors' copyrighted material. Keep real files local
> (`data/` is gitignored) and use open courseware (e.g. MIT OCW) for the public demo.
