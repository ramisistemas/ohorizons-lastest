const express = require('express');
const tasksService = require('../services/tasks.service');

const router = express.Router();

router.get('/tasks', async (req, res, next) => {
  try {
    res.json(await tasksService.list());
  } catch (err) {
    next(err);
  }
});

router.get('/tasks/:id', async (req, res, next) => {
  try {
    const task = await tasksService.get(req.params.id);
    if (!task) return res.status(404).json({ error: 'not_found' });
    res.json(task);
  } catch (err) {
    next(err);
  }
});

router.post('/tasks', async (req, res, next) => {
  try {
    const task = await tasksService.create(req.body);
    res.status(201).json(task);
  } catch (err) {
    next(err);
  }
});

router.patch('/tasks/:id', async (req, res, next) => {
  try {
    const task = await tasksService.update(req.params.id, req.body);
    if (!task) return res.status(404).json({ error: 'not_found' });
    res.json(task);
  } catch (err) {
    next(err);
  }
});

router.delete('/tasks/:id', async (req, res, next) => {
  try {
    const deleted = await tasksService.remove(req.params.id);
    if (!deleted) return res.status(404).json({ error: 'not_found' });
    res.status(204).send();
  } catch (err) {
    next(err);
  }
});

module.exports = router;
