"""Your tests go here (or in new tests/<folder>/test_*.py files).

Pick the fixture that matches what you want to test - they come from conftest.py:

    store / make_task   business logic only            -> fastest
    client              Python API via Flask, no socket -> fast
    api / live_server   real HTTP against python/node   -> run with --backend all

Folder markers are automatic: anything under tests/unit gets @unit, tests/api gets
@api, tests/contract gets @contract + @slow. Useful commands:

    pytest                               everything (contract tests hit the Python backend)
    pytest tests/test_my_feature.py -v   just this file
    pytest -m "not slow"                 skip tests that start servers
    pytest -m contract --backend all     contract tests against both backends
    pytest -k lifecycle -x --lf          by name, stop on first failure, last-failed first

Example skeletons (uncomment and edit):

# import pytest
#
# def test_something_in_the_store(store, make_task):
#     task = make_task("my task")
#     assert store.get(task.id).title == "my task"
#
# def test_something_in_the_api(client):
#     resp = client.post("/api/tasks", json={"title": "x"})
#     assert resp.status_code == 201
#
# def test_something_on_both_backends(api):
#     assert api.get("/health").json()["status"] == "ok"
"""
