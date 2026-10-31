import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app import api
from app.config import Settings
from app.models import Answer, Claim
from tests.conftest import GOOD_SUMMARY, FakeLLM


@pytest.fixture
def client(store, tmp_path, monkeypatch):
    monkeypatch.setattr(api, "settings", Settings(data_dir=tmp_path))
    llm = FakeLLM(
        summaries=[GOOD_SUMMARY],
        answers=[Answer(claims=[Claim(text="Merge sort runs in O(n log n) time.", slides=[1])])],
    )
    return TestClient(api.create_app(store, llm))


def test_upload_then_browse_then_ask(client, pdf_file):
    with pdf_file.open("rb") as fh:
        r = client.post(
            "/upload", data={"course": "CS 2"}, files={"file": ("lecture7.pdf", fh, "application/pdf")}
        )
    assert r.status_code == 200 and r.json()["supported"] == 3

    assert client.get("/courses").json() == [{"course": "CS 2", "decks": 1, "last_synced": None}]
    deck_id = client.get("/courses/CS 2/decks").json()[0]["id"]

    detail = client.get(f"/decks/{deck_id}").json()
    assert detail["report"]["passed"] and len(detail["summary"]["abstract"]) == 3
    assert "O(n log n)" in client.get(f"/decks/{deck_id}/slides/2").json()["text"]

    ans = client.post("/ask", json={"course": "CS 2", "question": "merge sort time"}).json()
    assert ans["claims"][0]["sources"][0]["slide"] == 2


def test_upload_rejects_wrong_type(client):
    r = client.post("/upload", data={"course": "CS 2"}, files={"file": ("x.txt", b"hi", "text/plain")})
    assert r.status_code == 400


def test_sync_without_canvas_is_clear_error(client):
    assert client.post("/sync").status_code == 400


def test_upload_corrupt_file_is_400(client):
    r = client.post("/upload", data={"course": "CS 2"}, files={"file": ("x.pdf", b"junk", "application/pdf")})
    assert r.status_code == 400


def test_frontend_schema_is_up_to_date(store):
    schema = api.create_app(store, None).openapi()
    committed = json.loads(Path("web/openapi.json").read_text())
    assert schema == committed, "run: python scripts/export_openapi.py && cd web && npm run gen:api"


def test_course_names_with_slashes_work(client, pdf_file):
    with pdf_file.open("rb") as fh:
        client.post("/upload", data={"course": "CS/MATH 1"}, files={"file": ("l.pdf", fh)})
    assert len(client.get("/courses/CS%2FMATH 1/decks").json()) == 1


class RejectingCanvas:
    def __init__(self, error):
        self.error = error

    def courses(self):
        raise self.error


@pytest.mark.parametrize(
    "error, message",
    [
        (httpx.HTTPStatusError("x", request=None, response=httpx.Response(401)), "rejected the token"),
        (httpx.HTTPStatusError("x", request=None, response=httpx.Response(500)), "status 500"),
        (httpx.ConnectError("x"), "Can't reach Canvas"),
    ],
)
def test_sync_failures_are_clear(store, tmp_path, monkeypatch, error, message):
    monkeypatch.setattr(api, "settings", Settings(data_dir=tmp_path))
    client = TestClient(api.create_app(store, FakeLLM(), canvas=RejectingCanvas(error)))
    r = client.post("/sync")
    assert r.status_code == 502 and message in r.json()["detail"]
    assert client.get("/config").json() == {"canvas": True}
