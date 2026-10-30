"""SQLite persistence: parsed decks, verified summaries, and which LMS files we've already seen."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import Deck, Summary, VerificationReport

SCHEMA = """
CREATE TABLE IF NOT EXISTS decks (
    id TEXT PRIMARY KEY, course TEXT NOT NULL, title TEXT NOT NULL,
    body TEXT NOT NULL, source_version TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS summaries (
    deck_id TEXT PRIMARY KEY REFERENCES decks(id), body TEXT NOT NULL,
    report TEXT NOT NULL, attempts INTEGER NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS traces (
    id INTEGER PRIMARY KEY, kind TEXT NOT NULL, subject TEXT NOT NULL,
    attempt INTEGER NOT NULL, body TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


class Store:
    def __init__(self, path: Path | str = ":memory:"):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.executescript(SCHEMA)

    # ---- decks -------------------------------------------------------------
    def save_deck(self, deck: Deck, source_version: str | None = None) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO decks (id, course, title, body, source_version) VALUES (?,?,?,?,?)",
            (deck.id, deck.course, deck.title, deck.model_dump_json(), source_version),
        )
        self.db.commit()

    def get_deck(self, deck_id: str) -> Deck | None:
        row = self.db.execute("SELECT body FROM decks WHERE id=?", (deck_id,)).fetchone()
        return Deck.model_validate_json(row[0]) if row else None

    def decks_for_course(self, course: str) -> list[Deck]:
        rows = self.db.execute(
            "SELECT body FROM decks WHERE course=? ORDER BY created_at DESC", (course,)
        ).fetchall()
        return [Deck.model_validate_json(r[0]) for r in rows]

    def courses(self) -> list[dict]:
        rows = self.db.execute(
            "SELECT course, COUNT(*) FROM decks GROUP BY course ORDER BY course"
        ).fetchall()
        return [{"course": c, "decks": n} for c, n in rows]

    def is_current(self, deck_id: str, source_version: str) -> bool:
        """True if we already have this exact version of an LMS file (skip re-processing)."""
        row = self.db.execute("SELECT source_version FROM decks WHERE id=?", (deck_id,)).fetchone()
        return bool(row) and row[0] == source_version

    # ---- summaries ---------------------------------------------------------
    def save_summary(self, deck_id: str, summary: Summary, report: VerificationReport, attempts: int) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO summaries (deck_id, body, report, attempts) VALUES (?,?,?,?)",
            (deck_id, summary.model_dump_json(), report.model_dump_json(), attempts),
        )
        self.db.commit()

    def get_summary(self, deck_id: str) -> dict | None:
        row = self.db.execute(
            "SELECT body, report, attempts FROM summaries WHERE deck_id=?", (deck_id,)
        ).fetchone()
        if not row:
            return None
        return {"summary": json.loads(row[0]), "report": json.loads(row[1]), "attempts": row[2]}

    # ---- traces ------------------------------------------------------------
    def save_trace(self, kind: str, subject: str, trace: list[dict]) -> None:
        """Keep every attempt and verifier report, for debugging and evals. `subject` is a deck or course."""
        self.db.executemany(
            "INSERT INTO traces (kind, subject, attempt, body) VALUES (?,?,?,?)",
            [(kind, subject, t["attempt"], json.dumps(t)) for t in trace],
        )
        self.db.commit()

    def get_traces(self, subject: str) -> list[dict]:
        rows = self.db.execute("SELECT body FROM traces WHERE subject=? ORDER BY id", (subject,)).fetchall()
        return [json.loads(r[0]) for r in rows]
