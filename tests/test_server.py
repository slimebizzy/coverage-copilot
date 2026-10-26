import os

os.environ["COPILOT_LLM"] = "fake"

from fastapi.testclient import TestClient  # noqa: E402

from app import server  # noqa: E402

server.pipeline.trace_path = None
client = TestClient(server.app)


def test_index_and_meta():
    assert client.get("/").status_code == 200
    meta = client.get("/api/meta").json()
    assert meta["offline"] is True and "adjuster" in meta["roles"]


def test_ask_returns_cited_answer():
    r = client.post("/api/ask", json={"question": "Is mold covered?", "role": "policyholder", "state": "OTHER"})
    body = r.json()
    assert r.status_code == 200 and body["status"] == "answered"
    assert body["sources"] and body["sources"][0]["chunk_id"].startswith("HO3")


def test_unknown_role_is_rejected():
    r = client.post("/api/ask", json={"question": "Is mold covered?", "role": "admin"})
    assert r.status_code == 422
