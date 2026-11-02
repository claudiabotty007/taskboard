"""REST API: /api/health and /api/tasks."""
from flask import Blueprint, current_app, jsonify, request

from . import __version__
from .store import TaskNotFound, TaskStore, ValidationError

api = Blueprint("api", __name__, url_prefix="/api")


def _store() -> TaskStore:
    return current_app.extensions["task_store"]


def _json_body() -> dict:
    body = request.get_json(silent=True)
    if body is None:
        if request.get_data():
            raise ValidationError("request body must be valid JSON")
        return {}
    if not isinstance(body, dict):
        raise ValidationError("request body must be a JSON object")
    return body


def _parse_bool(value):
    if value is None:
        return None
    if value.lower() in ("true", "1"):
        return True
    if value.lower() in ("false", "0"):
        return False
    raise ValidationError("done must be true or false")


@api.errorhandler(ValidationError)
def _bad_request(err):
    return jsonify(error=str(err)), 400


@api.errorhandler(TaskNotFound)
def _not_found(err):
    return jsonify(error=str(err)), 404


@api.get("/health")
def health():
    return jsonify(status="ok", backend="python", version=__version__)


@api.get("/stats")
def stats():
    return jsonify(_store().stats())


@api.get("/tasks")
def list_tasks():
    done = _parse_bool(request.args.get("done"))
    return jsonify([t.to_dict() for t in _store().list(done=done)])


@api.post("/tasks")
def create_task():
    task = _store().add(_json_body().get("title"))
    return jsonify(task.to_dict()), 201


@api.delete("/tasks")
def clear_tasks():
    _store().clear()
    return "", 204


@api.get("/tasks/<int:task_id>")
def get_task(task_id):
    return jsonify(_store().get(task_id).to_dict())


@api.patch("/tasks/<int:task_id>")
def update_task(task_id):
    body = _json_body()
    task = _store().update(task_id, title=body.get("title"), done=body.get("done"))
    return jsonify(task.to_dict())


@api.delete("/tasks/<int:task_id>")
def delete_task(task_id):
    _store().delete(task_id)
    return "", 204
