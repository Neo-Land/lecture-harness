"""Canvas sync with a fake LMS: only new or changed files get processed."""

import shutil

from app.pipeline import sync_canvas
from tests.conftest import GOOD_SUMMARY, FakeLLM


class FakeCanvas:
    def __init__(self, src, version="v1"):
        self.src, self.version, self.downloads = src, version, 0

    def courses(self):
        return [{"id": 1, "name": "CS 2"}]

    def lecture_files(self, course_id, limit=5):
        return [
            {
                "id": 99,
                "display_name": "lecture7.pdf",
                "updated_at": self.version,
                "content-type": "application/pdf",
            }
        ]

    def download(self, f, dest_dir):
        self.downloads += 1
        dest_dir.mkdir(parents=True, exist_ok=True)
        return shutil.copy(self.src, dest_dir / "99.pdf")


def test_sync_skips_unchanged_and_reprocesses_updated(pdf_file, store, tmp_path):
    canvas, llm = FakeCanvas(pdf_file), FakeLLM(summaries=[GOOD_SUMMARY] * 2)

    assert len(sync_canvas(canvas, store, llm, None, tmp_path)) == 1
    assert sync_canvas(canvas, store, llm, None, tmp_path) == []  # nothing new
    assert canvas.downloads == 1

    canvas.version = "v2"  # professor re-uploaded
    assert len(sync_canvas(canvas, store, llm, None, tmp_path)) == 1
    assert store.get_summary("canvas-99")["report"]["passed"]
