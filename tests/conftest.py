"""Shared pytest fixtures, command-line options and hooks.

Fixtures available to every test (no import needed):

    store        fresh in-memory TaskStore
    make_task    factory: make_task("title", done=False) -> Task, added to `store`
    app          Flask app wired to `store`
    client       Flask test client for `app`
    live_server  a running backend process -> LiveServer(backend, base_url)
                 parametrized by --backend (python | node | all)
    api          ApiClient bound to `live_server`; the board is emptied before each test

Command-line options:

    --backend {python,node,all}   which backend(s) the contract tests start (default: python)
    --base-url URL                test an already-running server instead of starting one
"""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import pytest
import requests

from taskboard import create_app
from taskboard.store import TaskStore

ROOT = Path(__file__).resolve().parents[1]
BACKENDS = ("python", "node")
FOLDER_MARKERS = {"unit": ["unit"], "api": ["api"], "contract": ["contract", "slow"]}


# --------------------------------------------------------------------------- hooks

def pytest_addoption(parser):
    group = parser.getgroup("taskboard")
    group.addoption(
        "--backend",
        choices=[*BACKENDS, "all"],
        default="python",
        help="backend(s) the contract tests run against (default: python)",
    )
    group.addoption(
        "--base-url",
        default=None,
        help="run contract tests against an already-running server, e.g. http://127.0.0.1:8000",
    )


def pytest_collection_modifyitems(config, items):
    """Mark tests by folder, so `pytest -m unit` works without decorating every test."""
    for item in items:
        for marker in FOLDER_MARKERS.get(item.path.parent.name, []):
            item.add_marker(marker)


def pytest_generate_tests(metafunc):
    """Run every test that uses `live_server` once per selected backend."""
    if "live_server" not in metafunc.fixturenames:
        return
    if metafunc.config.getoption("--base-url"):
        backends = ["external"]
    else:
        choice = metafunc.config.getoption("--backend")
        backends = list(BACKENDS) if choice == "all" else [choice]
    metafunc.parametrize("live_server", backends, indirect=True, scope="session")


# ------------------------------------------------------------- unit / api fixtures

@pytest.fixture
def store() -> TaskStore:
    return TaskStore()


@pytest.fixture
def make_task(store):
    """Factory fixture: call it as many times as a test needs."""

    def _make(title: str = "Sample task", done: bool = False):
        task = store.add(title)
        if done:
            store.update(task.id, done=True)
        return task

    return _make


@pytest.fixture
def app(store):
    return create_app({"TESTING": True, "STORE": store})


@pytest.fixture
def client(app):
    return app.test_client()


# --------------------------------------------------------- live-server fixtures

@dataclass(frozen=True)
class LiveServer:
    backend: str
    base_url: str


class ApiClient:
    """Small requests wrapper: api.get("/tasks") calls <base_url>/api/tasks."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", 5)
        return self.session.request(method, f"{self.base_url}/api{path}", **kwargs)

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def patch(self, path, **kwargs):
        return self.request("PATCH", path, **kwargs)

    def delete(self, path, **kwargs):
        return self.request("DELETE", path, **kwargs)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _server_command(backend: str) -> list[str]:
    if backend == "python":
        return [sys.executable, str(ROOT / "backend-python" / "run.py")]
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    if not (ROOT / "backend-node" / "node_modules").is_dir():
        pytest.skip("node backend is not built - run scripts/build.sh node (or build.ps1 -Backend node)")
    return [node, str(ROOT / "backend-node" / "src" / "server.js")]


def _wait_until_up(url: str, proc: subprocess.Popen, timeout: float = 15.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"server exited early with code {proc.returncode}")
        try:
            if requests.get(url, timeout=0.5).ok:
                return
        except requests.ConnectionError:
            pass
        time.sleep(0.1)
    raise TimeoutError(f"server did not answer {url} within {timeout}s")


@pytest.fixture(scope="session")
def live_server(request, tmp_path_factory):
    """Start the backend once per test session (setup), stop it at the end (teardown)."""
    base_url = request.config.getoption("--base-url")
    if base_url:
        base_url = base_url.rstrip("/")
        backend = requests.get(f"{base_url}/api/health", timeout=5).json()["backend"]
        yield LiveServer(backend, base_url)
        return

    backend = request.param
    port = _free_port()
    env = {**os.environ, "HOST": "127.0.0.1", "PORT": str(port)}
    env.pop("TASKBOARD_DATA_FILE", None)  # always in-memory
    log_path = tmp_path_factory.mktemp("servers") / f"{backend}.log"

    with open(log_path, "w") as log:
        proc = subprocess.Popen(_server_command(backend), cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        base_url = f"http://127.0.0.1:{port}"
        try:
            _wait_until_up(f"{base_url}/api/health", proc)
        except Exception as exc:
            proc.kill()
            pytest.fail(f"{backend} backend failed to start: {exc}\n{log_path.read_text()}")

        yield LiveServer(backend, base_url)

        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture
def api(live_server):
    client = ApiClient(live_server.base_url)
    client.delete("/tasks").raise_for_status()  # every test starts with an empty board
    yield client
    client.session.close()
