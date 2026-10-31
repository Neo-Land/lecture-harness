"""Public demo: read-only, rate limited, and license-cleared slide images only."""

import importlib.util
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import api
from app.api import AskLimiter
from app.config import Settings
from app.models import Answer, Claim
from tests.conftest import GOOD_SUMMARY, FakeLLM

spec = importlib.util.spec_from_file_location("seed_demo", Path("scripts/seed_demo.py"))
seed_demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed_demo)


@pytest.fixture
def demo(store, tmp_path, monkeypatch, sorting_deck):
    settings = Settings(data_dir=tmp_path, demo=True, demo_asks_per_minute=2, demo_asks_per_day=100)
    monkeypatch.setattr(api, "settings", settings)
    store.save_deck(sorting_deck)
    answers = [Answer(claims=[Claim(text="Merge sort.", slides=[1])]) for _ in range(5)]
    return TestClient(api.create_app(store, FakeLLM(answers=answers), canvas=object()))


def test_demo_refuses_writes_and_hides_canvas(demo):
    assert demo.post("/sync").status_code == 403
    assert demo.post("/upload", data={"course": "C"}, files={"file": ("a.pdf", b"x")}).status_code == 403
    assert demo.get("/config").json() == {"canvas": False, "demo": True}


def test_demo_rate_limits_questions(demo):
    ask = {"course": "CS 2", "question": "merge sort"}
    assert [demo.post("/ask", json=ask).status_code for _ in range(3)] == [200, 200, 429]


def test_question_length_is_limited_everywhere(demo):
    assert demo.post("/ask", json={"course": "CS 2", "question": "x" * 501}).status_code == 422


def test_limiter_minute_day_and_rollover():
    now = [0.0]
    limiter = AskLimiter(per_minute=1, per_day=2, clock=lambda: now[0])
    assert limiter.allow("a") and not limiter.allow("a")  # per visitor per minute
    assert limiter.allow("b") and not limiter.allow("c")  # daily cap is shared
    now[0] = 86400.0
    assert limiter.allow("a")  # new day


def test_seed_removes_excluded_images_and_sets_title(pdf_file, store, tmp_path):
    deck_file = tmp_path / "mit6_0001_lec2.pdf"
    deck_file.write_bytes(pdf_file.read_bytes())
    monkey_excluded = seed_demo.EXCLUDED_IMAGES
    seed_demo.EXCLUDED_IMAGES = {"mit6_0001_lec2": [2]}
    try:
        seed_demo.seed_deck(deck_file, store, FakeLLM(summaries=[GOOD_SUMMARY]), None, tmp_path / "img")
    finally:
        seed_demo.EXCLUDED_IMAGES = monkey_excluded
    deck = store.get_deck("mit6_0001_lec2")
    assert deck.title.startswith("Lecture 2") and deck.course == "MIT 6.0001"
    assert not deck.slide(2).has_image and deck.slide(1).has_image
    assert not (tmp_path / "img" / "mit6_0001_lec2" / "2.png").exists()
