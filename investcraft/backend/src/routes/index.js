const express = require('express');
const router = express.Router();

const authRoutes        = require('./auth');
const puzzleRoutes      = require('./puzzles');
const leaderboardRoutes = require('./leaderboard');
const userRoutes        = require('./users');

router.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'InvestCraft API',
    version: '1.0.0',
    timestamp: new Date().toISOString(),
  });
});

router.use('/auth',        authRoutes);
router.use('/puzzles',     puzzleRoutes);
router.use('/leaderboard', leaderboardRoutes);
router.use('/users',       userRoutes);

module.exports = router;
