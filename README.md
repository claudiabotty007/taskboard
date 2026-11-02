# Taskboard

A small full-stack task tracker whose backend exists in **two languages** behind one API:

| Part | Tech | Path |
|---|---|---|
| Frontend | HTML + CSS + vanilla JS (no build step) | `frontend/` |
| Backend #1 | Python 3.10+ / Flask | `backend-python/` |
| Backend #2 | Node.js 18+ / Express | `backend-node/` |
| Tests | pytest (both backends) + `node:test` | `tests/`, `backend-node/test/` |
| CI | Jenkins declarative pipeline, Linux + Windows matrix | `Jenkinsfile` |

Either backend serves the same frontend and implements the same REST contract, which the
pytest contract tests check against both.

## Quick start

**Windows (PowerShell)**

```powershell
.\scripts\build.ps1 -Backend all      # .venv + npm ci + dist\*.zip
.\scripts\test.ps1  -Backend all      # pytest + npm test, JUnit XML in reports\
.\scripts\run.ps1   -Backend python   # or -Backend node -> http://127.0.0.1:8000
```

If scripts are blocked, prefix with `powershell -ExecutionPolicy Bypass -File`.

**Linux (bash)**

```bash
./scripts/build.sh all                # .venv + npm ci + dist/*.tar.gz
./scripts/test.sh all                 # pytest + npm test, JUnit XML in reports/
./scripts/run.sh python               # or node -> http://127.0.0.1:8000
```

Environment variables: `PORT` (default 8000), `HOST` (default 127.0.0.1),
`TASKBOARD_DATA_FILE` (JSON file to persist tasks; in-memory when unset), `PYTHON`
(interpreter used to create `.venv`).

## API

| Method | Path | Body | Result |
|---|---|---|---|
| GET | `/api/health` | | `{"status","backend","version"}` |
| GET | `/api/stats` | | `{"total","done","open"}` |
| GET | `/api/tasks?done=true\|false` | | list of tasks |
| POST | `/api/tasks` | `{"title"}` | 201 + task |
| DELETE | `/api/tasks` | | 204, removes all tasks |
| GET | `/api/tasks/<id>` | | task or 404 |
| PATCH | `/api/tasks/<id>` | `{"title"?, "done"?}` | task |
| DELETE | `/api/tasks/<id>` | | 204 |

A task is `{"id": 1, "title": "...", "done": false, "created_at": "2026-01-01T12:00:00+00:00"}`.
Errors are always JSON: `{"error": "message"}` with 400 or 404.

## Tests

```text
tests/
  conftest.py            fixtures, --backend/--base-url options, auto-markers
  unit/test_store.py     business logic       (marker: unit)
  api/test_routes.py     Flask test client    (marker: api)
  contract/              real HTTP, both backends (markers: contract, slow)
  test_my_feature.py     your scratchpad + skeletons
```

pytest features already in use, to copy from: fixtures (function and session scope,
setup/teardown with `yield`), a factory fixture (`make_task`), fixture parametrization
(`live_server` via `pytest_generate_tests`), `@pytest.mark.parametrize` with `ids`,
`pytest.raises(match=...)`, `tmp_path`, `tmp_path_factory`, `monkeypatch`, `skipif`,
strict `xfail`, `pytest.skip` from a fixture, custom command-line options, and registered
markers applied by a collection hook.

```bash
pytest                              # all tests; contract tests hit the Python backend
pytest -m unit                      # just the fast ones
pytest -m "not slow"                # skip tests that start a server
pytest -m contract --backend all    # contract tests against python AND node
pytest --base-url http://127.0.0.1:8000 -m contract   # against a server you started
```

Run pytest with the venv's interpreter (`.venv\Scripts\python -m pytest` on Windows,
`.venv/bin/python -m pytest` on Linux) or activate the venv first.

## Jenkins

1. Create a **Pipeline** (or Multibranch Pipeline) job pointing at this repository, script
   path `Jenkinsfile`.
2. Provide agents labelled `linux` and `windows` with git, Python 3.10+ (`python3` on Linux,
   `python` on Windows) and Node 18+ on `PATH`.
3. Push. The job polls SCM every ~5 minutes; add a webhook for instant builds.

The pipeline runs a matrix of **{linux, windows} x {python, node}**: build -> test ->
publish JUnit results -> archive `dist/` packages. The HEAD commit message can narrow it:

| Directive in commit message | Effect |
|---|---|
| `[skip ci]` | no build/test stages run |
| `[python]` / `[node]` | only that backend |
| `[linux]` / `[windows]` | only that platform |

Manual runs use the `BACKEND` and `PLATFORM` parameters instead.

## Extending

Adding an endpoint touches the same places in both languages:

1. `backend-python/taskboard/store.py` + `routes.py`
2. `backend-node/src/store.js` + `app.js`
3. a contract test in `tests/contract/` (proves both behave the same)
4. unit/API tests for the Python side, `backend-node/test/` for the Node side
5. the API table above
