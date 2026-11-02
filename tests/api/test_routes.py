"""Flask test-client tests for the Python backend - no server process, no socket.

Shows: the `client` fixture (built from `app`, built from `store`), arranging
state through fixtures, status/JSON assertions, and parametrize over bad input.
"""
import pytest

from taskboard import __version__


def test_health(client):
    resp = client.get("/api/health")

    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok", "backend": "python", "version": __version__}


def test_index_serves_frontend(client):
    resp = client.get("/")

    assert resp.status_code == 200
    assert b"<title>Taskboard</title>" in resp.data


def test_create_task(client, store):
    resp = client.post("/api/tasks", json={"title": "  new task  "})

    assert resp.status_code == 201
    body = resp.get_json()
    assert body["title"] == "new task"
    assert body["done"] is False
    assert store.get(body["id"]).title == "new task"


@pytest.mark.parametrize(
    "payload",
    [{}, {"title": ""}, {"title": 5}, ["not", "an", "object"]],
    ids=["missing-title", "empty-title", "int-title", "json-array"],
)
def test_create_task_rejects_bad_payload(client, store, payload):
    resp = client.post("/api/tasks", json=payload)

    assert resp.status_code == 400
    assert "error" in resp.get_json()
    assert len(store) == 0


def test_create_task_rejects_malformed_json(client):
    resp = client.post("/api/tasks", data="{not json", content_type="application/json")

    assert resp.status_code == 400
    assert resp.get_json() == {"error": "request body must be valid JSON"}


def test_list_tasks_filters_by_done(client, make_task):
    make_task("open")
    make_task("closed", done=True)

    resp = client.get("/api/tasks?done=true")

    assert [t["title"] for t in resp.get_json()] == ["closed"]


def test_list_tasks_rejects_bad_filter(client):
    assert client.get("/api/tasks?done=maybe").status_code == 400


def test_patch_task(client, make_task):
    task = make_task("rename me")

    resp = client.patch(f"/api/tasks/{task.id}", json={"title": "renamed", "done": True})

    assert resp.status_code == 200
    assert resp.get_json()["title"] == "renamed"
    assert resp.get_json()["done"] is True


def test_delete_task(client, make_task):
    task = make_task()

    assert client.delete(f"/api/tasks/{task.id}").status_code == 204
    assert client.get(f"/api/tasks/{task.id}").status_code == 404


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_unknown_task_returns_404(client, method):
    resp = getattr(client, method)("/api/tasks/999", json={})

    assert resp.status_code == 404
    assert resp.get_json() == {"error": "task 999 not found"}
