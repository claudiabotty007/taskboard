'use strict';
// REST API: /api/health and /api/tasks. Mirrors backend-python/taskboard/routes.py.
const path = require('node:path');
const express = require('express');
const { version } = require('../package.json');
const { TaskNotFound, TaskStore, ValidationError } = require('./store');

const DEFAULT_FRONTEND_DIR = path.resolve(__dirname, '..', '..', 'frontend');

function jsonBody(req) {
  const body = req.body === undefined ? {} : req.body;
  if (typeof body !== 'object' || body === null || Array.isArray(body)) {
    throw new ValidationError('request body must be a JSON object');
  }
  return body;
}

function parseBool(value) {
  if (value === undefined) return null;
  if (['true', '1'].includes(value.toLowerCase())) return true;
  if (['false', '0'].includes(value.toLowerCase())) return false;
  throw new ValidationError('done must be true or false');
}

function createApp({
  store = new TaskStore(process.env.TASKBOARD_DATA_FILE || null),
  frontendDir = process.env.TASKBOARD_FRONTEND_DIR || DEFAULT_FRONTEND_DIR,
} = {}) {
  const app = express();
  const api = express.Router();
  api.use(express.json());

  api.get('/health', (req, res) => res.json({ status: 'ok', backend: 'node', version }));

  api.get('/tasks', (req, res) => res.json(store.list(parseBool(req.query.done))));

  api.post('/tasks', (req, res) => res.status(201).json(store.add(jsonBody(req).title)));

  api.delete('/tasks', (req, res) => {
    store.clear();
    res.status(204).end();
  });

  api.get('/tasks/:id(\\d+)', (req, res) => res.json(store.get(Number(req.params.id))));

  api.patch('/tasks/:id(\\d+)', (req, res) => {
    const { title, done } = jsonBody(req);
    res.json(store.update(Number(req.params.id), { title, done }));
  });

  api.delete('/tasks/:id(\\d+)', (req, res) => {
    store.delete(Number(req.params.id));
    res.status(204).end();
  });

  api.use((req, res) => res.status(404).json({ error: `no such endpoint: ${req.method} ${req.originalUrl}` }));

  // eslint-disable-next-line no-unused-vars
  api.use((err, req, res, next) => {
    if (err instanceof ValidationError) return res.status(400).json({ error: err.message });
    if (err instanceof TaskNotFound) return res.status(404).json({ error: err.message });
    if (err.type === 'entity.parse.failed') return res.status(400).json({ error: 'request body must be valid JSON' });
    console.error(err);
    return res.status(500).json({ error: 'internal server error' });
  });

  app.use('/api', api);
  app.use(express.static(frontendDir));
  return app;
}

module.exports = { createApp };
