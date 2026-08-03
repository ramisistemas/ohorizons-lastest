const request = require('supertest');
const app = require('../src/index');
const { pool } = require('../src/db/pool');
const { ensureSchema } = require('../src/db/queries');

beforeAll(async () => {
  await ensureSchema();
});

afterAll(async () => {
  await pool.end();
});

describe('health endpoints', () => {
  it('GET /health returns healthy', async () => {
    const res = await request(app).get('/health');
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('healthy');
  });
});

describe('tasks CRUD', () => {
  let createdId;

  it('POST /tasks creates a task', async () => {
    const res = await request(app)
      .post('/tasks')
      .send({ title: 'test task', notes: null, done: false });
    expect(res.status).toBe(201);
    expect(res.body.title).toBe('test task');
    createdId = res.body.id;
  });

  it('GET /tasks lists tasks', async () => {
    const res = await request(app).get('/tasks');
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body)).toBe(true);
  });

  it('PATCH /tasks/:id updates the task', async () => {
    const res = await request(app)
      .patch(`/tasks/${createdId}`)
      .send({ title: 'test task', notes: null, done: true });
    expect(res.status).toBe(200);
    expect(res.body.done).toBe(true);
  });

  it('DELETE /tasks/:id removes the task', async () => {
    const res = await request(app).delete(`/tasks/${createdId}`);
    expect(res.status).toBe(204);
  });
});
