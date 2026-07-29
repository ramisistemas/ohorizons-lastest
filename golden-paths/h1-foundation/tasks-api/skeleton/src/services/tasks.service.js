const queries = require('../db/queries');

class ValidationError extends Error {}

const list = () => queries.listTasks();

const get = (id) => queries.getTask(id);

const create = ({ title, notes, done }) => {
  if (!title) throw new ValidationError('title_required');
  return queries.createTask({ title, notes, done });
};

const update = async (id, { title, notes, done }) => {
  if (!title) throw new ValidationError('title_required');
  const existing = await queries.getTask(id);
  if (!existing) return null;
  return queries.updateTask(id, { title, notes, done });
};

const remove = async (id) => {
  const rowCount = await queries.deleteTask(id);
  return rowCount > 0;
};

module.exports = { list, get, create, update, remove, ValidationError };
