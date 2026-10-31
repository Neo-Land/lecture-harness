# 0003 — Render slide images at ingest, as files on disk

- **Status:** accepted
- **Date:** 2026-10-30

## Context
A citation is only useful if the student can see the slide it points to, including diagrams that text
extraction misses. Slides are private course material and must stay out of git.

## Options considered
1. Render on request: no storage used, but every click repeats the work and a moved source file breaks it.
2. Render at ingest to PNG files under `data/`: costs some disk, serves instantly, needs no source file later.
3. Store PNGs in SQLite: one file to manage, but a bloated database and awkward serving.

## Decision
Option 2 at 110 DPI, readable on a laptop at a modest file size. PDFs render with PyMuPDF. PPTX needs
LibreOffice to convert first; without it the app falls back to text only rather than failing the ingest.

## Consequences
- `Slide.has_image` tells the frontend whether to show an image or the text.
- PPTX images depend on a tool outside `requirements.txt`, so the full Docker image installs LibreOffice.
  The demo image only has PDFs and leaves it out.
- Images are a separate best-effort step: a render failure never loses the deck or its summary.
