const express = require('express');
const router = express.Router();
const { getIstDateString } = require('../utils/date');

const authRoutes = require('./auth');
const puzzleRoutes = require('./puzzles');
const leaderboardRoutes = require('./leaderboard');
const userRoutes = require('./users');
const missionsRoutes = require('./missions');
const educationRoutes = require('./education');


router.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'InvestBrand API',
    version: '1.1.0',
    timestamp: getIstDateString(),
  });
});

router.use('/auth', authRoutes);
router.use('/puzzles', puzzleRoutes);
router.use('/leaderboard', leaderboardRoutes);
router.use('/users', userRoutes);
router.use('/missions', missionsRoutes);
router.use('/education', educationRoutes);


module.exports = router;
