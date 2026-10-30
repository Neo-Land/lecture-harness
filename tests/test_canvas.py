"""CanvasClient against a mocked Canvas API (no network)."""

import httpx
import pytest

from app.lms.canvas import CanvasClient

BASE = "https://school.instructure.com"
PDF = "application/pdf"


def handler(request: httpx.Request) -> httpx.Response:
    path, params = request.url.path, request.url.params
    if request.headers.get("Authorization") != "Bearer tok":
        return httpx.Response(401)
    if path == "/api/v1/courses":
        return httpx.Response(
            200,
            json=[
                {"id": 1, "course_code": "CS 2"},
                {"id": 2, "name": "Old Course", "access_restricted_by_date": True},
            ],
        )
    if path == "/api/v1/courses/1/files" and params.get("page") != "2":
        nxt = f'<{BASE}/api/v1/courses/1/files?page=2>; rel="next"'
        return httpx.Response(
            200,
            headers={"Link": nxt},
            json=[
                {"id": 10, "content-type": PDF, "url": f"{BASE}/dl/10"},
                {"id": 11, "content-type": "image/png", "url": f"{BASE}/dl/11"},
            ],
        )
    if path == "/api/v1/courses/1/files":
        return httpx.Response(200, json=[{"id": 12, "content-type": PDF, "url": f"{BASE}/dl/12"}])
    if path.startswith("/dl/"):
        return httpx.Response(200, content=b"%PDF-fake")
    return httpx.Response(404)


def make_client(token="tok"):
    http = httpx.Client(transport=httpx.MockTransport(handler), headers={"Authorization": f"Bearer {token}"})
    return CanvasClient(BASE, token, client=http)


def test_courses_skips_restricted():
    assert make_client().courses() == [{"id": 1, "name": "CS 2"}]


def test_lecture_files_follow_pagination_and_filter_types():
    assert [f["id"] for f in make_client().lecture_files(1)] == [10, 12]
    assert [f["id"] for f in make_client().lecture_files(1, limit=1)] == [10]


def test_download_writes_file(tmp_path):
    path = make_client().download({"id": 10, "content-type": PDF, "url": f"{BASE}/dl/10"}, tmp_path / "c1")
    assert path.name == "10.pdf" and path.read_bytes() == b"%PDF-fake"


def test_bad_token_raises():
    with pytest.raises(httpx.HTTPStatusError):
        make_client("wrong").courses()
