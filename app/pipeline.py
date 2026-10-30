"""Sync new lecture files from the LMS, parse them, and summarize them through the harness."""

from __future__ import annotations

import logging
from pathlib import Path

from .harness import summarize_deck
from .llm import LLM
from .parsing import parse_file
from .store import Store
from .verifier import Judge

log = logging.getLogger("pipeline")


def ingest_file(
    path: Path,
    course: str,
    store: Store,
    llm: LLM,
    judge: Judge | None,
    deck_id: str | None = None,
    source_version: str | None = None,
    max_revisions: int = 2,
) -> dict:
    deck = parse_file(path, course, deck_id)
    store.save_deck(deck, source_version)
    result = summarize_deck(deck, llm, judge, max_revisions)
    store.save_summary(deck.id, result.output, result.report, result.attempts)
    return {
        "deck_id": deck.id,
        "title": deck.title,
        "attempts": result.attempts,
        "supported": result.report.claims_supported,
        "total": result.report.claims_total,
    }


def sync_canvas(
    canvas,
    store: Store,
    llm: LLM,
    judge: Judge | None,
    files_dir: Path,
    per_course: int = 5,
    max_revisions: int = 2,
) -> list[dict]:
    """Process only files that are new or changed since the last run."""
    done = []
    for course in canvas.courses():
        for f in canvas.lecture_files(course["id"], limit=per_course):
            deck_id, version = f"canvas-{f['id']}", f.get("updated_at", "")
            if store.is_current(deck_id, version):
                continue
            path = canvas.download(f, files_dir / str(course["id"]))
            log.info("new file %s in %s", f.get("display_name"), course["name"])
            done.append(
                ingest_file(
                    path,
                    course["name"],
                    store,
                    llm,
                    judge,
                    deck_id=deck_id,
                    source_version=version,
                    max_revisions=max_revisions,
                )
            )
    return done
