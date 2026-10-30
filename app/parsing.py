"""Turn PDF / PPTX lecture files into numbered slides."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pymupdf as fitz
from pptx import Presentation

from .models import Deck, Slide

SUPPORTED = {".pdf", ".pptx"}


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _clean(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def parse_pdf(path: Path) -> list[Slide]:
    with fitz.open(path) as doc:
        return [Slide(number=i + 1, text=_clean(page.get_text())) for i, page in enumerate(doc)]


def parse_pptx(path: Path) -> list[Slide]:
    slides = []
    for i, s in enumerate(Presentation(str(path)).slides):
        parts = []
        for shape in s.shapes:
            if shape.has_text_frame:
                parts.append(shape.text_frame.text)
            if getattr(shape, "has_table", False) and shape.has_table:
                for row in shape.table.rows:
                    parts.append(" | ".join(c.text for c in row.cells))
        if s.has_notes_slide:  # speaker notes often hold the real explanation
            parts.append(s.notes_slide.notes_text_frame.text)
        slides.append(Slide(number=i + 1, text=_clean("\n".join(parts))))
    return slides


def parse_file(path: Path, course: str, deck_id: str | None = None) -> Deck:
    ext = path.suffix.lower()
    if ext not in SUPPORTED:
        raise ValueError(f"Unsupported file type: {ext}")
    slides = parse_pdf(path) if ext == ".pdf" else parse_pptx(path)
    return Deck(id=deck_id or file_hash(path), course=course, title=path.stem, slides=slides)
