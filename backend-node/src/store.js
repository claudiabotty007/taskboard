'use strict';
// In-memory task store with optional JSON-file persistence.
// Mirrors backend-python/taskboard/store.py - keep the two in sync.
const fs = require('node:fs');
const path = require('node:path');

const MAX_TITLE_LENGTH = 200;

class ValidationError extends Error {}
class TaskNotFound extends Error {}

function now() {
  // Same shape as Python's isoformat(timespec="seconds"): 2026-01-01T12:00:00+00:00
  return new Date().toISOString().slice(0, 19) + '+00:00';
}

function validateTitle(title) {
  if (typeof title !== 'string') throw new ValidationError('title must be a string');
  const trimmed = title.trim();
  if (!trimmed) throw new ValidationError('title must not be empty');
  if (trimmed.length > MAX_TITLE_LENGTH) {
    throw new ValidationError(`title must be at most ${MAX_TITLE_LENGTH} characters`);
  }
  return trimmed;
}

class TaskStore {
  constructor(dataFile = null) {
    this.tasks = new Map();
    this.nextId = 1;
    this.dataFile = dataFile;
    if (dataFile && fs.existsSync(dataFile)) this._load();
  }

  get size() {
    return this.tasks.size;
  }

  list(done = null) {
    const all = [...this.tasks.values()].sort((a, b) => a.id - b.id);
    return done === null ? all : all.filter((t) => t.done === done);
  }

  get(id) {
    const task = this.tasks.get(id);
    if (!task) throw new TaskNotFound(`task ${id} not found`);
    return task;
  }

  add(title) {
    const task = { id: this.nextId, title: validateTitle(title), done: false, created_at: now() };
    this.tasks.set(task.id, task);
    this.nextId += 1;
    this._save();
    return task;
  }

  update(id, { title, done } = {}) {
    const task = this.get(id);
    // Validate everything before mutating so a bad request changes nothing.
    const newTitle = title !== undefined && title !== null ? validateTitle(title) : task.title;
    if (done !== undefined && done !== null && typeof done !== 'boolean') {
      throw new ValidationError('done must be a boolean');
    }
    task.title = newTitle;
    if (typeof done === 'boolean') task.done = done;
    this._save();
    return task;
  }

  delete(id) {
    this.get(id);
    this.tasks.delete(id);
    this._save();
  }

  clear() {
    this.tasks.clear();
    this._save();
  }

  stats() {
    const tasks = this.list();
    const done = tasks.filter((t) => t.done).length;
    return { total: tasks.length, done, open: tasks.length - done };
  }

  _load() {
    const data = JSON.parse(fs.readFileSync(this.dataFile, 'utf8'));
    this.tasks = new Map((data.tasks || []).map((t) => [t.id, t]));
    this.nextId = data.next_id || Math.max(0, ...this.tasks.keys()) + 1;
  }

  _save() {
    if (!this.dataFile) return;
    fs.mkdirSync(path.dirname(this.dataFile), { recursive: true });
    const payload = { next_id: this.nextId, tasks: this.list() };
    const tmp = `${this.dataFile}.tmp`;
    fs.writeFileSync(tmp, JSON.stringify(payload, null, 2), 'utf8');
    fs.renameSync(tmp, this.dataFile);
  }
}

module.exports = { MAX_TITLE_LENGTH, TaskNotFound, TaskStore, ValidationError, validateTitle };
