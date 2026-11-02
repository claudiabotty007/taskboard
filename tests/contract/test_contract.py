"""Black-box HTTP tests that BOTH backends must pass.

Each test talks to a real server process over HTTP (see `live_server` and `api`
in conftest.py), so the same file verifies the Python and the Node implementation:

    pytest -m contract --backend all
"""
import pytest

TASK_FIELDS = {"id", "title", "done", "created_at"}


def test_health_identifies_backend(api, live_server):
    body = api.get("/health").json()

    assert body["status"] == "ok"
    assert body["backend"] == live_server.backend


def test_task_lifecycle(api):
    created = api.post("/tasks", json={"title": "contract"})
    assert created.status_code == 201
    task = created.json()
    assert set(task) == TASK_FIELDS

    updated = api.patch(f"/tasks/{task['id']}", json={"done": True})
    assert updated.json()["done"] is True
    assert [t["id"] for t in api.get("/tasks?done=true").json()] == [task["id"]]

    assert api.delete(f"/tasks/{task['id']}").status_code == 204
    assert api.get(f"/tasks/{task['id']}").status_code == 404


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        ({}, "title must be a string"),
        ({"title": "   "}, "title must not be empty"),
        ({"title": "x" * 201}, "title must be at most 200 characters"),
        ([1, 2], "request body must be a JSON object"),
    ],
    ids=["missing", "blank", "too-long", "array"],
)
def test_validation_errors_match(api, payload, error):
    resp = api.post("/tasks", json=payload)

    assert resp.status_code == 400
    assert resp.json() == {"error": error}


def test_unknown_task_error_is_json(api):
    resp = api.get("/tasks/999")

    assert resp.status_code == 404
    assert resp.json() == {"error": "task 999 not found"}
