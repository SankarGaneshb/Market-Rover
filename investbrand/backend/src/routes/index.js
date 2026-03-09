const express = require('express');
const router = express.Router();
const { getIstDateString } = require('../utils/date');

const authRoutes = require('./auth');
const puzzleRoutes = require('./puzzles');
const leaderboardRoutes = require('./leaderboard');
const userRoutes = require('./users');

router.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'InvestCraft API',
    version: '1.1.0',
    timestamp: getIstDateString(),
  });
});

router.use('/auth', authRoutes);
router.use('/puzzles', puzzleRoutes);
router.use('/leaderboard', leaderboardRoutes);
router.use('/users', userRoutes);

module.exports = router;
