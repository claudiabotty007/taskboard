'use strict';
// Node-side unit tests (run with `npm test`). The cross-backend HTTP tests live in tests/contract (pytest).
const test = require('node:test');
const assert = require('node:assert/strict');
const { TaskNotFound, TaskStore, ValidationError } = require('../src/store');

test('add assigns incrementing ids', () => {
  const store = new TaskStore();
  assert.equal(store.add('first').id, 1);
  assert.equal(store.add('second').id, 2);
});

test('titles are trimmed and validated', () => {
  const store = new TaskStore();
  assert.equal(store.add('  padded  ').title, 'padded');
  assert.throws(() => store.add('   '), ValidationError);
  assert.throws(() => store.add(42), ValidationError);
});

test('get throws TaskNotFound for unknown ids', () => {
  assert.throws(() => new TaskStore().get(999), TaskNotFound);
});

test('list filters by done', () => {
  const store = new TaskStore();
  store.add('a');
  store.update(store.add('b').id, { done: true });
  assert.deepEqual(store.list(true).map((t) => t.title), ['b']);
  assert.deepEqual(store.list(false).map((t) => t.title), ['a']);
});
