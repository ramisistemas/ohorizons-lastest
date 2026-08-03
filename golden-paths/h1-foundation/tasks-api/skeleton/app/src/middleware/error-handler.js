const { ValidationError } = require('../services/tasks.service');

// eslint-disable-next-line no-unused-vars -- Express solo reconoce middleware de error con 4 argumentos
module.exports = (err, req, res, next) => {
  if (err instanceof ValidationError) {
    return res.status(400).json({ error: err.message });
  }
  console.error(err.stack);
  res.status(500).json({ error: 'internal_error' });
};
