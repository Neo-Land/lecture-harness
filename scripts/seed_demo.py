"""Fill a database with the open-license eval decks for the public demo: python scripts/seed_demo.py
Uses the configured model, so set HARNESS_OFFLINE=true to keep it free."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings, validate_settings  # noqa: E402
from app.llm import make_llm  # noqa: E402
from app.pipeline import ingest_file  # noqa: E402
from app.store import Store  # noqa: E402
from evals.decks import fetch_decks  # noqa: E402

COURSE = "MIT 6.0001"
TITLES = {
    "mit6_0001_lec1": "Lecture 1: What is computation?",
    "mit6_0001_lec2": "Lecture 2: Branching and iteration",
    "mit6_0001_lec3": "Lecture 3: Strings, guess-and-check, bisection",
    "mit6_0001_lec4": "Lecture 4: Decomposition, abstraction, functions",
    "mit6_0001_lec5": "Lecture 5: Tuples, lists, aliasing, cloning",
}
# Slides with third-party images MIT excludes from its license (see evals/SOURCES.md)
EXCLUDED_IMAGES = {"mit6_0001_lec1": [18], "mit6_0001_lec2": [14, 15]}


def seed_deck(path: Path, store: Store, llm, judge, images_dir: Path) -> None:
    """Ingest one deck under its readable title, removing images MIT's license doesn't cover."""
    name = path.stem
    ingest_file(path, COURSE, store, llm, judge, deck_id=name, images_dir=images_dir)
    deck = store.get_deck(name)
    deck.title = TITLES[name]
    for number in EXCLUDED_IMAGES.get(name, []):
        deck.slide(number).has_image = False
        (images_dir / name / f"{number}.png").unlink(missing_ok=True)
    store.save_deck(deck)


if __name__ == "__main__":
    validate_settings(settings)
    llm, judge = make_llm(settings)
    store = Store(settings.db_path)
    for deck_path in fetch_decks():
        seed_deck(deck_path, store, llm, judge, settings.images_dir)
    print(f"Seeded {len(store.decks_for_course(COURSE))} decks into {settings.db_path}")
