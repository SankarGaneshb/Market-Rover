jest.mock('../config/database', () => ({
    getPool: jest.fn(),
}));

jest.mock('../middleware/auth', () => ({
    authenticate: (req, res, next) => {
        req.user = { id: 1, email: 'test@example.com' };
        next();
    }
}));

const request = require('supertest');
const express = require('express');
const { getPool } = require('../config/database');
const puzzleRoutes = require('../routes/puzzles');
const { getIstDateString } = require('../utils/date');

const app = express();
app.use(express.json());
app.use('/api/puzzles', puzzleRoutes);

describe('Puzzle Routes', () => {
    let mockQuery;

    beforeEach(() => {
        mockQuery = jest.fn();
        getPool.mockReturnValue({ query: mockQuery });
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    describe('GET /daily', () => {
        it('should return scheduled puzzle for today', async () => {
            const mockPuzzle = { id: 1, brand_id: 101, ticker: 'RELIANCE', scheduled_date: getIstDateString() };
            mockQuery.mockResolvedValueOnce({ rows: [mockPuzzle] });

            const res = await request(app).get('/api/puzzles/daily');
            expect(res.statusCode).toBe(200);
            expect(res.body.brand_id).toBe(101);
        });

        it('should fallback to voted brand puzzle if no puzzle scheduled today', async () => {
            mockQuery
                .mockResolvedValueOnce({ rows: [] }) // No scheduled puzzle
                .mockResolvedValueOnce({ rows: [{ brand_id: 102, vote_count: 5 }] }) // Most voted brand
                .mockResolvedValueOnce({ rows: [{ id: 2, brand_id: 102, ticker: 'TCS' }] }) // Found puzzle for brand
                .mockResolvedValueOnce({ rows: [] }); // Update call

            const res = await request(app).get('/api/puzzles/daily');
            expect(res.statusCode).toBe(200);
            expect(res.body.brand_id).toBe(102);
        });

        it('should assign a random open puzzle if no votes exist', async () => {
            mockQuery
                .mockResolvedValueOnce({ rows: [] }) // No scheduled puzzle
                .mockResolvedValueOnce({ rows: [] }) // No votes
                .mockResolvedValueOnce({ rows: [{ id: 3, brand_id: 103, ticker: 'HDFCBANK' }] }) // Random unscheduled puzzle
                .mockResolvedValueOnce({ rows: [] }); // Update call

            const res = await request(app).get('/api/puzzles/daily');
            expect(res.statusCode).toBe(200);
            expect(res.body.brand_id).toBe(103);
        });

        it('should handle db errors on /daily', async () => {
            mockQuery.mockRejectedValue(new Error('DB Error'));

            const res = await request(app).get('/api/puzzles/daily');
            expect(res.statusCode).toBe(500);
            expect(res.body.error).toBe('Failed to fetch puzzle');
        });
    });

    describe('POST /vote', () => {
        it('should post a vote successfully', async () => {
            mockQuery.mockResolvedValue({ rows: [] });

            const res = await request(app).post('/api/puzzles/vote').send({ brandId: 104 });
            expect(res.statusCode).toBe(200);
            expect(res.body.success).toBe(true);
        });

        it('should return 400 if brandId missing', async () => {
            const res = await request(app).post('/api/puzzles/vote').send({});
            expect(res.statusCode).toBe(400);
        });

        it('should handle db error on /vote', async () => {
            mockQuery.mockRejectedValue(new Error('DB Error'));

            const res = await request(app).post('/api/puzzles/vote').send({ brandId: 104 });
            expect(res.statusCode).toBe(500);
        });
    });

    describe('GET /', () => {
        it('should fetch paginated puzzles', async () => {
            const mockPuzzles = [{ id: 1, ticker: 'ITC' }];
            mockQuery.mockResolvedValue({ rows: mockPuzzles });

            const res = await request(app).get('/api/puzzles?page=2');
            expect(res.statusCode).toBe(200);
            expect(res.body.puzzles[0].ticker).toBe('ITC');
            expect(res.body.page).toBe(2);
            expect(mockQuery.mock.calls[0][1][1]).toBe(10); // Offset should be 10 for page 2
        });

        it('should handle db errors on /', async () => {
            mockQuery.mockRejectedValue(new Error('DB Error'));
            const res = await request(app).get('/api/puzzles');
            expect(res.statusCode).toBe(500);
        });
    });

    describe('POST /:id/complete', () => {
        it('should save game session result correctly and update streak given prev day', async () => {
            // First mock is insert/update game session
            mockQuery.mockResolvedValueOnce({ rows: [] });
            // Second is aggregate score sum
            mockQuery.mockResolvedValueOnce({ rows: [{ real_total: 500 }] });
            // Third is getting last played
            const yesterdayDate = new Date();
            yesterdayDate.setDate(yesterdayDate.getDate() - 1);
            const yesterday = getIstDateString(yesterdayDate);
            mockQuery.mockResolvedValueOnce({ rows: [{ last_played: yesterday, streak: 5 }] });
            // Fourth is update users table
            mockQuery.mockResolvedValueOnce({ rows: [] });

            const res = await request(app).post('/api/puzzles/1/complete').send({ score: 100, movesUsed: 5, timeTaken: 30 });

            expect(res.statusCode).toBe(200);
            expect(res.body.success).toBe(true);
            expect(res.body.streak).toBe(6); // 5 + 1
            expect(res.body.realTotal).toBe(500);
        });

        it('should maintain streak if already played today', async () => {
            mockQuery.mockResolvedValueOnce({ rows: [] });
            mockQuery.mockResolvedValueOnce({ rows: [{ real_total: 600 }] });
            const today = getIstDateString();
            mockQuery.mockResolvedValueOnce({ rows: [{ last_played: today, streak: 6 }] });
            mockQuery.mockResolvedValueOnce({ rows: [] });

            const res = await request(app).post('/api/puzzles/2/complete').send({ score: 100 });

            expect(res.statusCode).toBe(200);
            expect(res.body.streak).toBe(6);
        });

        it('should handle db error on completion', async () => {
            mockQuery.mockRejectedValue(new Error('DB error on completion'));
            const res = await request(app).post('/api/puzzles/3/complete').send({ score: 100 });
            expect(res.statusCode).toBe(500);
        });
    });
});
