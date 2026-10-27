import os

os.environ["COPILOT_LLM"] = "fake"

from fastapi.testclient import TestClient  # noqa: E402

from app import server  # noqa: E402

server.pipeline.trace_path = None
server.FEEDBACK_PATH = server.Path(os.environ.get("TMPDIR", "/tmp")) / "copilot-test-feedback.jsonl"
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


def test_meta_lists_documents_with_access_metadata():
    docs = {d["id"]: d for d in client.get("/api/meta").json()["documents"]}
    assert docs["CHG"]["internal"] is True and docs["CHG"]["roles"] == ["adjuster"]
    assert docs["CA-HO-AE"]["jurisdiction"] == "CA"


def test_sources_carry_the_full_section_for_the_ui():
    body = client.post("/api/ask", json={"question": "Is mold covered?", "role": "policyholder"}).json()
    src = body["sources"][0]
    assert src["blocks"] and src["cited_texts"] and src["heading"] and src["doc_title"]


def test_feedback_is_recorded_and_validated():
    assert client.post("/api/feedback", json={"trace_id": "0123456789ab", "rating": "down", "note": "wrong limit"}).json() == {"ok": True}
    assert client.post("/api/feedback", json={"trace_id": "nope", "rating": "down"}).status_code == 422


def test_section_endpoint_enforces_access():
    ok = client.get("/api/section", params={"id": "HO3 §2.5", "role": "policyholder"})
    assert ok.status_code == 200 and ok.json()["heading"].startswith("Coverage D")
    assert client.get("/api/section", params={"id": "CHG §2.1", "role": "policyholder"}).status_code == 404
    assert client.get("/api/section", params={"id": "CHG §2.1", "role": "adjuster"}).status_code == 200
    assert client.get("/api/section", params={"id": "CA-HO-AE §1.1", "role": "policyholder", "state": "TX"}).status_code == 404
