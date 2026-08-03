const express = require('express');
const cors = require('cors');
const prometheus = require('prom-client');
const env = require('./config/env');
const { ensureSchema } = require('./db/queries');
const tasksRouter = require('./routes/tasks');
const requestMetrics = require('./middleware/request-metrics');
const errorHandler = require('./middleware/error-handler');

const app = express();

prometheus.collectDefaultMetrics();

app.use(cors({ origin: env.allowedOrigin }));
app.use(express.json());
app.use(requestMetrics);

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

app.get('/ready', async (req, res) => {
  try {
    const { pool } = require('./db/pool');
    await pool.query('select 1');
    res.json({ status: 'ready', timestamp: new Date().toISOString() });
  } catch (err) {
    res.status(503).json({ status: 'not_ready', error: err.message });
  }
});

app.get('/metrics', async (req, res) => {
  res.set('Content-Type', prometheus.register.contentType);
  res.end(await prometheus.register.metrics());
});

app.use(tasksRouter);

app.use(errorHandler);

if (require.main === module) {
  ensureSchema()
    .then(() => {
      app.listen(env.port, () => {
        console.log(`${{ values.name }} listening on ${env.port}`);
      });
    })
    .catch((err) => {
      console.error('Failed to ensure schema', err);
      process.exit(1);
    });
}

module.exports = app;
