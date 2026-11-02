"""Unit tests for taskboard.store - pure Python, no HTTP.

Shows: plain asserts, fixtures and a factory fixture, @pytest.mark.parametrize
(with ids), pytest.raises(match=...), tmp_path, monkeypatch, skipif and xfail.
"""
import sys
from pathlib import Path

import pytest

from taskboard import create_app
from taskboard.store import MAX_TITLE_LENGTH, TaskNotFound, TaskStore, ValidationError, validate_title


def test_new_store_is_empty(store):
    assert len(store) == 0
    assert store.list() == []


def test_add_assigns_incrementing_ids(store):
    first = store.add("first")
    second = store.add("second")

    assert (first.id, second.id) == (1, 2)
    assert first.done is False


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("buy milk", "buy milk"),
        ("  padded  ", "padded"),
        ("x" * MAX_TITLE_LENGTH, "x" * MAX_TITLE_LENGTH),
        ("café ✓", "café ✓"),
    ],
    ids=["plain", "strips-whitespace", "max-length", "unicode"],
)
def test_validate_title_accepts(raw, expected):
    assert validate_title(raw) == expected


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        (None, "must be a string"),
        (42, "must be a string"),
        ("", "must not be empty"),
        ("   ", "must not be empty"),
        ("x" * (MAX_TITLE_LENGTH + 1), "at most"),
    ],
    ids=["none", "int", "empty", "blank", "too-long"],
)
def test_validate_title_rejects(raw, message):
    with pytest.raises(ValidationError, match=message):
        validate_title(raw)


def test_get_missing_task_raises(store):
    with pytest.raises(TaskNotFound) as exc_info:
        store.get(999)

    assert "999" in str(exc_info.value)


def test_update_marks_done(store, make_task):
    task = make_task("write tests")

    store.update(task.id, done=True)

    assert store.get(task.id).done is True


def test_invalid_update_changes_nothing(store, make_task):
    task = make_task("original")

    with pytest.raises(ValidationError):
        store.update(task.id, title="renamed", done="yes")

    assert store.get(task.id).title == "original"


@pytest.mark.parametrize(
    ("done", "expected_titles"),
    [(None, ["a", "b", "c"]), (True, ["b"]), (False, ["a", "c"])],
)
def test_list_filters_by_done(store, make_task, done, expected_titles):
    make_task("a")
    make_task("b", done=True)
    make_task("c")

    assert [t.title for t in store.list(done=done)] == expected_titles


def test_delete_removes_task(store, make_task):
    task = make_task()

    store.delete(task.id)

    assert len(store) == 0
    with pytest.raises(TaskNotFound):
        store.delete(task.id)


def test_tasks_persist_across_instances(tmp_path):
    data_file = tmp_path / "tasks.json"
    TaskStore(data_file).add("survive a restart")

    reloaded = TaskStore(data_file)

    assert [t.title for t in reloaded.list()] == ["survive a restart"]
    assert reloaded.add("next").id == 2  # the id counter is persisted too


def test_create_app_reads_data_file_from_env(monkeypatch, tmp_path):
    data_file = tmp_path / "from-env.json"
    monkeypatch.setenv("TASKBOARD_DATA_FILE", str(data_file))

    app = create_app()
    app.extensions["task_store"].add("hello")

    assert data_file.exists()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-style paths only matter on Windows")
def test_data_file_accepts_backslash_paths(tmp_path):
    data_file = str(tmp_path / "nested" / "tasks.json").replace("/", "\\")

    TaskStore(data_file).add("x")

    assert Path(data_file).exists()


@pytest.mark.xfail(reason="feature idea: reject duplicate titles - not implemented yet", strict=True)
def test_duplicate_titles_are_rejected(store):
    store.add("same")
    with pytest.raises(ValidationError):
        store.add("same")
