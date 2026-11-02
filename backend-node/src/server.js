'use strict';
// Start the Node backend: node backend-node/src/server.js  (env: HOST, PORT)
const { createApp } = require('./app');

const host = process.env.HOST || '127.0.0.1';
const port = Number(process.env.PORT || 8000);

createApp().listen(port, host, () => {
  console.log(`Taskboard (node) listening on http://${host}:${port}`);
});
