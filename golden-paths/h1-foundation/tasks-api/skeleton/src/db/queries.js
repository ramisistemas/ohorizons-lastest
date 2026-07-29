const { pool } = require('./pool');

const ensureSchema = () =>
  pool.query(`
    create table if not exists public.tasks (
      id bigint generated always as identity primary key,
      title text not null,
      notes text,
      done boolean not null default false,
      created_at timestamptz not null default now()
    );
  `);

const listTasks = () =>
  pool.query('select * from tasks order by created_at desc').then((r) => r.rows);

const getTask = (id) =>
  pool.query('select * from tasks where id = $1', [id]).then((r) => r.rows[0]);

const createTask = ({ title, notes, done }) =>
  pool
    .query(
      'insert into tasks (title, notes, done) values ($1, $2, $3) returning *',
      [title, notes ?? null, done ?? false],
    )
    .then((r) => r.rows[0]);

const updateTask = (id, { title, notes, done }) =>
  pool
    .query(
      'update tasks set title = $1, notes = $2, done = $3 where id = $4 returning *',
      [title, notes ?? null, done ?? false, id],
    )
    .then((r) => r.rows[0]);

const deleteTask = (id) =>
  pool.query('delete from tasks where id = $1', [id]).then((r) => r.rowCount);

module.exports = { ensureSchema, listTasks, getTask, createTask, updateTask, deleteTask };
