"""Taskboard - Python (Flask) backend."""
import os
from pathlib import Path

from flask import Flask, jsonify, request

from .store import TaskStore

__version__ = "1.0.0"

DEFAULT_FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


def create_app(config: dict | None = None) -> Flask:
    """Application factory.

    Optional config keys (environment variable fallback in brackets):
      STORE         a ready-made TaskStore (handy in tests)
      DATA_FILE     JSON file for persistence; in-memory when unset  [TASKBOARD_DATA_FILE]
      FRONTEND_DIR  directory holding index.html                     [TASKBOARD_FRONTEND_DIR]
    """
    config = dict(config or {})
    frontend_dir = (
        config.get("FRONTEND_DIR")
        or os.environ.get("TASKBOARD_FRONTEND_DIR")
        or DEFAULT_FRONTEND_DIR
    )
    app = Flask(__name__, static_folder=str(frontend_dir), static_url_path="")
    app.config.update(config)

    data_file = config.get("DATA_FILE") or os.environ.get("TASKBOARD_DATA_FILE")
    store = config.get("STORE")  # not `or`: an empty store has len 0 and is falsy
    app.extensions["task_store"] = store if store is not None else TaskStore(data_file)

    from .routes import api

    app.register_blueprint(api)

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.errorhandler(404)
    def not_found(err):
        # Unknown /api routes never reach the blueprint's handlers, so answer them here.
        if request.path.startswith("/api/"):
            return jsonify(error=f"no such endpoint: {request.method} {request.full_path.rstrip('?')}"), 404
        return err

    return app
