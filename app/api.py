"""HTTP API the Next.js frontend talks to.  Run: uvicorn app.api:app --reload"""

from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings
from .harness import answer_question
from .parsing import SUPPORTED
from .pipeline import ingest_file, sync_canvas
from .store import Store


class AskRequest(BaseModel):
    course: str
    question: str


def create_app(store: Store, llm, judge=None, canvas=None) -> FastAPI:
    app = FastAPI(title="Lecture Harness")
    app.add_middleware(
        CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"]
    )

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/courses")
    def courses():
        return store.courses()

    @app.get("/courses/{course}/decks")
    def decks(course: str):
        return [
            {"id": d.id, "title": d.title, "slides": len(d.slides)} for d in store.decks_for_course(course)
        ]

    @app.get("/decks/{deck_id}")
    def deck(deck_id: str):
        d = store.get_deck(deck_id)
        if not d:
            raise HTTPException(404, "deck not found")
        return {"deck": d.model_dump(), **(store.get_summary(deck_id) or {})}

    @app.get("/decks/{deck_id}/slides/{n}")
    def slide(deck_id: str, n: int):
        d = store.get_deck(deck_id)
        s = d.slide(n) if d else None
        if not s:
            raise HTTPException(404, "slide not found")
        return s.model_dump()

    @app.post("/upload")
    def upload(course: str = Form(...), file: UploadFile = File(...)):
        """Manual upload: lets you use the app without Canvas access."""
        ext = Path(file.filename or "").suffix.lower()
        if ext not in SUPPORTED:
            raise HTTPException(400, f"only {sorted(SUPPORTED)} supported")
        dest = settings.files_dir / "uploads" / Path(file.filename).name
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as fh:
            shutil.copyfileobj(file.file, fh)
        return ingest_file(dest, course, store, llm, judge, max_revisions=settings.max_revisions)

    @app.post("/sync")
    def sync():
        if canvas is None:
            raise HTTPException(400, "Canvas not configured (set CANVAS_BASE_URL and CANVAS_TOKEN)")
        return sync_canvas(
            canvas, store, llm, judge, settings.files_dir, max_revisions=settings.max_revisions
        )

    @app.post("/ask")
    def ask(req: AskRequest):
        decks = store.decks_for_course(req.course)
        if not decks:
            raise HTTPException(404, "no lectures for that course yet")
        result, cites = answer_question(req.question, decks, llm, judge)
        ans = result.output
        return {
            "insufficient_evidence": ans.insufficient_evidence,
            "claims": [
                {"text": c.text, "sources": [vars(cites[n]) for n in c.slides if n in cites]}
                for c in ans.claims
            ],
            "report": result.report.model_dump(),
        }

    return app


def _default_app() -> FastAPI:
    from .llm import ClaudeJudge, ClaudeLLM

    canvas = None
    if settings.canvas_base_url and settings.canvas_token:
        from .lms.canvas import CanvasClient

        canvas = CanvasClient(settings.canvas_base_url, settings.canvas_token)
    judge = ClaudeJudge() if settings.use_judge else None
    return create_app(Store(settings.db_path), ClaudeLLM(), judge, canvas)


def __getattr__(name):  # lazy so importing app.api in tests doesn't need an API key
    if name == "app":
        return _default_app()
    raise AttributeError(name)
