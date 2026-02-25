jest.mock('../config/database', () => ({
    getPool: jest.fn(),
}));

const request = require('supertest');
const express = require('express');
const { getPool } = require('../config/database');
const leaderboardRoutes = require('../routes/leaderboard');

const app = express();
app.use(express.json());
app.use('/api/leaderboard', leaderboardRoutes);

describe('Leaderboard Routes', () => {
    let mockQuery;

    beforeEach(() => {
        mockQuery = jest.fn();
        getPool.mockReturnValue({ query: mockQuery });
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    it('should fetch all-time leaderboard by default', async () => {
        const mockData = [{ id: 1, name: 'User1', score: 100 }];
        mockQuery.mockResolvedValue({ rows: mockData });

        const res = await request(app).get('/api/leaderboard');
        expect(res.statusCode).toBe(200);
        expect(res.body.leaderboard).toEqual(mockData);
        expect(res.body.type).toBe('all-time');
        expect(mockQuery.mock.calls[0][0]).toContain('ORDER BY total_score DESC');
    });

    it('should fetch daily leaderboard', async () => {
        const mockData = [{ id: 1, name: 'User1', score: 50 }];
        mockQuery.mockResolvedValue({ rows: mockData });

        const res = await request(app).get('/api/leaderboard?type=daily');
        expect(res.statusCode).toBe(200);
        expect(res.body.leaderboard).toEqual(mockData);
        expect(res.body.type).toBe('daily');
        expect(mockQuery.mock.calls[0][0]).toContain('WHERE p.scheduled_date = $1');
    });

    it('should fetch weekly leaderboard', async () => {
        const mockData = [{ id: 1, name: 'User1', score: 200 }];
        mockQuery.mockResolvedValue({ rows: mockData });

        const res = await request(app).get('/api/leaderboard?type=weekly');
        expect(res.statusCode).toBe(200);
        expect(res.body.leaderboard).toEqual(mockData);
        expect(res.body.type).toBe('weekly');
        expect(mockQuery.mock.calls[0][0]).toContain('WHERE gs.played_at >= NOW() - INTERVAL \'7 days\'');
    });

    it('should handle db errors gracefully', async () => {
        mockQuery.mockRejectedValue(new Error('DB Error'));

        const res = await request(app).get('/api/leaderboard');
        expect(res.statusCode).toBe(500);
        expect(res.body.error).toBe('Failed to fetch leaderboard');
    });
});
