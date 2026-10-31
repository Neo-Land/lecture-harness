"""CLI end to end, offline: real parsing and verification with the extractive stand-in."""

import json
import logging

import pymupdf as fitz

from app.__main__ import main
from app.harness import summarize_deck
from app.llm import ExtractiveLLM
from app.logs import JsonFormatter
from app.models import Deck, Slide
from app.parsing import parse_file
from app.pipeline import ingest_file
from tests.conftest import FakeLLM
from tests.test_pipeline import FakeCanvas


def test_ingest_then_ask_offline(pdf_file, store, capsys):
    llm = ExtractiveLLM()
    assert main(["ingest", str(pdf_file), "--course", "CS 2"], llm=llm, store=store) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["supported"] == out["total"] == 4 and out["needs_ocr"] == []
    assert store.get_traces(out["deck_id"])

    assert main(["ask", "merge sort", "--course", "CS 2"], llm=llm, store=store) == 0
    assert "lecture7 slide" in capsys.readouterr().out


def test_ask_not_covered_and_unknown_course(pdf_file, store, capsys):
    llm = ExtractiveLLM()
    main(["ingest", str(pdf_file), "--course", "CS 2"], llm=llm, store=store)
    capsys.readouterr()
    assert main(["ask", "photosynthesis", "--course", "CS 2"], llm=llm, store=store) == 0
    assert "Not covered in the slides." in capsys.readouterr().out
    assert main(["ask", "anything", "--course", "Nope"], llm=llm, store=store) == 1


def test_bad_input_is_a_clear_error(store, tmp_path, capsys):
    llm = ExtractiveLLM()
    assert main(["ingest", str(tmp_path / "gone.pdf"), "--course", "C"], llm=llm, store=store) == 2
    (tmp_path / "notes.txt").write_text("hi")
    assert main(["ingest", str(tmp_path / "notes.txt"), "--course", "C"], llm=llm, store=store) == 2
    assert "Unsupported" in capsys.readouterr().err


def _blank_pdf(path, texts):
    doc = fitz.open()
    for text in texts:
        page = doc.new_page()
        if text:
            page.insert_text((72, 72), text)
    doc.save(path)
    return path


def test_scanned_pages_are_flagged(tmp_path):
    deck = parse_file(_blank_pdf(tmp_path / "s.pdf", ["Real text", ""]), "C")
    assert [s.needs_ocr for s in deck.slides] == [False, True]


def test_fully_scanned_deck_never_calls_the_model(tmp_path, store):
    path = _blank_pdf(tmp_path / "s.pdf", ["", ""])
    out = ingest_file(path, "C", store, FakeLLM(), None)  # FakeLLM has no scripted output: a call would raise
    assert out["needs_ocr"] == [1, 2] and out["attempts"] == 0


def test_extractive_output_passes_the_verifier(sorting_deck):
    assert summarize_deck(sorting_deck, ExtractiveLLM()).report.passed


def test_extractive_skips_blank_slides():
    deck = Deck(id="x", course="c", title="t", slides=[Slide(number=1, text=""), Slide(number=2, text="Hi")])
    assert [c.slides for c in ExtractiveLLM().summarize(deck, []).abstract] == [[2]]


def test_json_formatter_includes_extra_fields():
    record = logging.LogRecord("harness", logging.INFO, "f", 1, "harness_attempt", None, None)
    record.deck, record.attempt = "d1", 2
    entry = json.loads(JsonFormatter().format(record))
    assert entry["msg"] == "harness_attempt" and entry["deck"] == "d1" and entry["attempt"] == 2


def test_sync_command(pdf_file, store, capsys):
    canvas = FakeCanvas(pdf_file)
    assert main(["sync"], llm=ExtractiveLLM(), store=store, canvas=canvas) == 0
    assert json.loads(capsys.readouterr().out)[0]["deck_id"] == "canvas-99"


def test_sync_without_canvas_is_a_clear_error(store, capsys):
    assert main(["sync"], llm=ExtractiveLLM(), store=store) == 2
    assert "CANVAS_BASE_URL" in capsys.readouterr().err
