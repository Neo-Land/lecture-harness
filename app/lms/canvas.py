"""Minimal Canvas LMS client using the official REST API and a personal access token.
(Canvas: Account -> Settings -> New Access Token. Some schools disable this; check first.)

Swap this module out for another LMS by implementing the same three methods.
"""

from __future__ import annotations

from pathlib import Path

import httpx

LECTURE_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
}


class CanvasClient:
    def __init__(self, base_url: str, token: str, client: httpx.Client | None = None):
        self.base = base_url.rstrip("/") + "/api/v1"
        self.http = client or httpx.Client(
            headers={"Authorization": f"Bearer {token}"}, timeout=30, follow_redirects=True
        )

    def _paged(self, url: str, params: dict | None = None) -> list[dict]:
        out, next_url = [], url
        while next_url:
            r = self.http.get(next_url, params=params)
            r.raise_for_status()
            out.extend(r.json())
            next_url, params = r.links.get("next", {}).get("url"), None
        return out

    def courses(self) -> list[dict]:
        rows = self._paged(f"{self.base}/courses", {"enrollment_state": "active", "per_page": 50})
        return [
            {"id": c["id"], "name": c.get("course_code") or c.get("name")}
            for c in rows
            if "id" in c and not c.get("access_restricted_by_date")
        ]

    def lecture_files(self, course_id: int, limit: int = 20) -> list[dict]:
        """Most recently updated PDF/PPTX files in a course."""
        rows = self._paged(
            f"{self.base}/courses/{course_id}/files", {"sort": "updated_at", "order": "desc", "per_page": 50}
        )
        files = [f for f in rows if f.get("content-type") in LECTURE_TYPES]
        return files[:limit]

    def download(self, file: dict, dest_dir: Path) -> Path:
        dest_dir.mkdir(parents=True, exist_ok=True)
        ext = LECTURE_TYPES[file["content-type"]]
        path = dest_dir / f"{file['id']}{ext}"
        with self.http.stream("GET", file["url"]) as r:
            r.raise_for_status()
            with path.open("wb") as fh:
                for chunk in r.iter_bytes():
                    fh.write(chunk)
        return path
