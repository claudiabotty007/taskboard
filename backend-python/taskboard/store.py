"""In-memory task store with optional JSON-file persistence."""
from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

MAX_TITLE_LENGTH = 200


class ValidationError(ValueError):
    """Invalid user input (the API maps it to HTTP 400)."""


class TaskNotFound(LookupError):
    """Unknown task id (the API maps it to HTTP 404)."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Task:
    id: int
    title: str
    done: bool = False
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return asdict(self)


def validate_title(title) -> str:
    """Return the cleaned-up title or raise ValidationError."""
    if not isinstance(title, str):
        raise ValidationError("title must be a string")
    title = title.strip()
    if not title:
        raise ValidationError("title must not be empty")
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError(f"title must be at most {MAX_TITLE_LENGTH} characters")
    return title


class TaskStore:
    """Thread-safe task collection. Persists to `data_file` when one is given."""

    def __init__(self, data_file: str | Path | None = None):
        self._lock = threading.RLock()
        self._tasks: dict[int, Task] = {}
        self._next_id = 1
        self.data_file = Path(data_file) if data_file else None
        if self.data_file and self.data_file.exists():
            self._load()

    def __len__(self) -> int:
        return len(self._tasks)

    def list(self, done: bool | None = None) -> list[Task]:
        with self._lock:
            tasks = sorted(self._tasks.values(), key=lambda t: t.id)
        if done is None:
            return tasks
        return [t for t in tasks if t.done is done]

    def get(self, task_id: int) -> Task:
        try:
            return self._tasks[task_id]
        except KeyError:
            raise TaskNotFound(f"task {task_id} not found") from None

    def add(self, title) -> Task:
        title = validate_title(title)
        with self._lock:
            task = Task(id=self._next_id, title=title)
            self._tasks[task.id] = task
            self._next_id += 1
            self._save()
        return task

    def update(self, task_id: int, *, title=None, done=None) -> Task:
        with self._lock:
            task = self.get(task_id)
            # Validate everything before mutating so a bad request changes nothing.
            new_title = validate_title(title) if title is not None else task.title
            if done is not None and not isinstance(done, bool):
                raise ValidationError("done must be a boolean")
            task.title = new_title
            if done is not None:
                task.done = done
            self._save()
        return task

    def delete(self, task_id: int) -> None:
        with self._lock:
            self.get(task_id)
            del self._tasks[task_id]
            self._save()

    def clear(self) -> None:
        with self._lock:
            self._tasks.clear()
            self._save()

    def stats(self) -> dict:
        tasks = self.list()
        done = sum(t.done for t in tasks)
        return {"total": len(tasks), "done": done, "open": len(tasks) - done}

    def _load(self) -> None:
        data = json.loads(self.data_file.read_text(encoding="utf-8"))
        self._tasks = {t["id"]: Task(**t) for t in data.get("tasks", [])}
        self._next_id = data.get("next_id", max(self._tasks, default=0) + 1)

    def _save(self) -> None:
        if not self.data_file:
            return
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {"next_id": self._next_id, "tasks": [t.to_dict() for t in self.list()]}
        tmp = self.data_file.with_name(self.data_file.name + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(self.data_file)
