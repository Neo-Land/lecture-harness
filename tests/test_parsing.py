import pytest

from app.models import Slide
from app.parsing import _strip_boilerplate, parse_file


def test_pdf_slides_are_numbered_and_keep_text(pdf_file):
    deck = parse_file(pdf_file, course="CS 2")
    assert [s.number for s in deck.slides] == [1, 2, 3, 4]
    assert "O(n log n)" in deck.slide(2).text
    assert "0.42 seconds" in deck.slide(4).text


def test_pptx_reads_body_notes_and_tables(pptx_file):
    deck = parse_file(pptx_file, course="CS 2")
    assert len(deck.slides) == 3
    assert "O(1)" in deck.slide(1).text
    assert "chaining" in deck.slide(1).text  # speaker notes
    assert "0.75" in deck.slide(2).text
    assert "Array | O(n)" in deck.slide(3).text  # table rows


def test_same_file_gets_same_id(pdf_file):
    assert parse_file(pdf_file, "CS 2").id == parse_file(pdf_file, "CS 2").id


def test_rejects_unsupported(tmp_path):
    f = tmp_path / "notes.txt"
    f.write_text("hi")
    with pytest.raises(ValueError):
        parse_file(f, "CS 2")


@pytest.mark.parametrize("name", ["bad.pdf", "bad.pptx"])
def test_corrupt_file_is_a_clear_error(tmp_path, name):
    f = tmp_path / name
    f.write_bytes(b"not really a document")
    with pytest.raises(ValueError, match="Could not read"):
        parse_file(f, "CS 2")


def test_footers_and_page_numbers_do_not_count_as_evidence():
    slides = [Slide(number=i, text=f"Topic {i * 11}\nCS 101 LECTURE 1\n{i}") for i in range(1, 5)]
    cleaned = _strip_boilerplate(slides)
    assert cleaned[1].text == "Topic 22"
