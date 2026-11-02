// Taskboard frontend - plain JS, talks to whichever backend served it via /api.
const state = { tasks: [], filter: 'all' };
const $ = (selector) => document.querySelector(selector);

async function request(method, path, body) {
  const res = await fetch(`/api${path}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return null;
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data;
}

function showError(message) {
  const el = $('#error');
  el.textContent = message;
  el.hidden = !message;
}

async function refresh() {
  state.tasks = await request('GET', '/tasks');
  render();
}

// Run a mutation, then reload the list; surface API errors in the UI.
async function run(action) {
  try {
    await action();
    showError('');
    await refresh();
  } catch (err) {
    showError(err.message);
  }
}

function renderTask(task) {
  const li = document.createElement('li');
  li.classList.toggle('done', task.done);

  const checkbox = document.createElement('input');
  checkbox.type = 'checkbox';
  checkbox.checked = task.done;
  checkbox.setAttribute('aria-label', `Mark "${task.title}" as done`);
  checkbox.addEventListener('change', () =>
    run(() => request('PATCH', `/tasks/${task.id}`, { done: checkbox.checked })));

  const title = document.createElement('span');
  title.className = 'title';
  title.textContent = task.title;

  const remove = document.createElement('button');
  remove.type = 'button';
  remove.className = 'remove';
  remove.textContent = '✕';
  remove.setAttribute('aria-label', `Delete "${task.title}"`);
  remove.addEventListener('click', () => run(() => request('DELETE', `/tasks/${task.id}`)));

  li.append(checkbox, title, remove);
  return li;
}

function render() {
  const visible = state.tasks.filter(
    (t) => state.filter === 'all' || (state.filter === 'done') === t.done);

  const list = $('#tasks');
  list.replaceChildren(...visible.map(renderTask));
  if (!visible.length) {
    const empty = document.createElement('li');
    empty.className = 'empty';
    empty.textContent = state.tasks.length ? 'Nothing here.' : 'No tasks yet - add one above.';
    list.append(empty);
  }

  const open = state.tasks.filter((t) => !t.done).length;
  $('#summary').textContent = `${open} open · ${state.tasks.length - open} done`;

  for (const button of document.querySelectorAll('[data-filter]')) {
    button.setAttribute('aria-pressed', String(button.dataset.filter === state.filter));
  }
}

$('#new-task').addEventListener('submit', (event) => {
  event.preventDefault();
  const input = $('#title');
  run(async () => {
    await request('POST', '/tasks', { title: input.value });
    input.value = '';
  });
});

for (const button of document.querySelectorAll('[data-filter]')) {
  button.addEventListener('click', () => {
    state.filter = button.dataset.filter;
    render();
  });
}

(async function init() {
  try {
    const health = await request('GET', '/health');
    $('#backend').textContent = `${health.backend} backend · v${health.version}`;
    await refresh();
  } catch (err) {
    $('#backend').textContent = 'offline';
    showError(`Cannot reach the API: ${err.message}`);
  }
})();
