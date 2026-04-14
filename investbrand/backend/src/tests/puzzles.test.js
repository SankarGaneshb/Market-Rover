jest.mock('../config/database', () => ({
    getPool: jest.fn(),
}));

jest.mock('../middleware/auth', () => ({
    authenticate: (req, res, next) => {
        req.user = { id: 1, email: 'test@example.com' };
        next();
    }
}));

jest.mock('../agents/puzzleAgent', () => ({
    generateInitialClues: jest.fn(),
    evaluateGuess: jest.fn(),
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
        const mockClient = {
            query: mockQuery,
            release: jest.fn()
        };
        getPool.mockReturnValue({
            query: mockQuery,
            connect: jest.fn().mockResolvedValue(mockClient)
        });
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    describe('GET /daily', () => {
        it('should return voted brand puzzle even if one is scheduled today', async () => {
            mockQuery
                .mockResolvedValueOnce({ rows: [{ brand_id: 102, vote_count: 5 }] }) // 1. Winner Query
                .mockResolvedValueOnce({ rows: [{ id: 2, brand_id: 102, ticker: 'TCS' }] }); // 2. Found Puzzle for 102

            const res = await request(app).get('/api/puzzles/daily');
            expect(res.statusCode).toBe(200);
            expect(res.body.brand_id).toBe(102);
            expect(res.body.selectionMethod).toBe('voted');
            expect(res.body.voteCount).toBe(5);
        });

        it('should fallback to scheduled puzzle if no votes exist', async () => {
             mockQuery
                .mockResolvedValueOnce({ rows: [] }) // 1. Check votes (NONE)
                .mockResolvedValueOnce({ rows: [{ id: 1, brand_id: 101, ticker: 'RELIANCE' }] }) // 2. Check schedule (FOUND)
                .mockResolvedValueOnce({ rows: [] }); // 3. Update call

            const res = await request(app).get('/api/puzzles/daily');
            expect(res.statusCode).toBe(200);
            expect(res.body.brand_id).toBe(101);
            expect(res.body.selectionMethod).toBe('scheduled');
            expect(res.body.voteCount).toBe(0);
        });

        it('should assign a random open puzzle if no votes and no schedule exist', async () => {
             mockQuery
                .mockResolvedValueOnce({ rows: [] }) // 1. Check votes
                .mockResolvedValueOnce({ rows: [] }) // 2. Check schedule
                .mockResolvedValueOnce({ rows: [{ id: 3, brand_id: 103, ticker: 'HDFCBANK' }] }) // 3. Random
                .mockResolvedValueOnce({ rows: [] }); // 4. Update call

            const res = await request(app).get('/api/puzzles/daily');
            expect(res.statusCode).toBe(200);
            expect(res.body.brand_id).toBe(103);
            expect(res.body.selectionMethod).toBe('lucky_draw');
        });

        it('should handle db errors on /daily', async () => {
            mockQuery.mockRejectedValue(new Error('DB Error'));

            const res = await request(app).get('/api/puzzles/daily');
            expect(res.statusCode).toBe(500);
            expect(res.body.error).toBe('Failed to fetch puzzle: DB Error');
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

    describe('POST /:id/feedback', () => {
        it('should save feedback successfully', async () => {
            mockQuery.mockResolvedValue({ rows: [] });

            const res = await request(app)
                .post('/api/puzzles/1/feedback')
                .send({ category: 'puzzle', rating: 'too_hard' });

            expect(res.statusCode).toBe(200);
            expect(res.body.success).toBe(true);
        });

        it('should return 400 if category or rating is missing', async () => {
            const res = await request(app)
                .post('/api/puzzles/1/feedback')
                .send({ category: 'puzzle' });

            expect(res.statusCode).toBe(400);
            expect(res.body.error).toBe('category and rating are required');
        });

        it('should gracefully swallow db errors on feedback (return 200)', async () => {
            mockQuery.mockRejectedValue(new Error('DB Error'));

            const res = await request(app)
                .post('/api/puzzles/1/feedback')
                .send({ category: 'logo', rating: 'blurry' });

            // The route intentionally swallows DB errors to not block the UI
            expect(res.statusCode).toBe(200);
            expect(res.body.success).toBe(true);
        });
    });

    describe('GET /:id/clues', () => {
        const { generateInitialClues } = require('../agents/puzzleAgent');

        it('should return clues for a puzzle', async () => {
            // Mock get puzzle query
            mockQuery.mockResolvedValueOnce({
                rows: [{ id: 10, ticker: 'RELIANCE', company_name: 'Reliance Industries', sector: 'Energy' }]
            });
            // Mock get clues from DB (empty, to trigger generation)
            mockQuery.mockResolvedValueOnce({ rows: [] });
            // Mock Gemini generation
            generateInitialClues.mockResolvedValue({
                wordCloud: "Energy, Jio, Refinery",
                clue1: "Big Oil",
                clue2: "Huge Digital",
                clue3: "Fortune 500"
            });
            // Mock save to DB
            mockQuery.mockResolvedValueOnce({ rows: [] });

            const res = await request(app).get('/api/puzzles/10/clues');
            expect(res.statusCode).toBe(200);
            expect(res.body.clues.wordCloud).toBe("Energy, Jio, Refinery");
            expect(generateInitialClues).toHaveBeenCalled();
        });

        it('should return cached clues if available', async () => {
            // Note: Using ID 10 again might hit the cache if previous test succeeded
            mockQuery.mockResolvedValueOnce({
                rows: [{ id: 10, ticker: 'RELIANCE', company_name: 'Reliance Industries', sector: 'Energy' }]
            });
            // If cache hit, it won't even query the DB for clues or call the agent

            const res = await request(app).get('/api/puzzles/10/clues');
            expect(res.statusCode).toBe(200);
            expect(res.body.clues.wordCloud).toBe("Energy, Jio, Refinery"); // From previous test
            expect(generateInitialClues).not.toHaveBeenCalled();
        });

        it('should return 404 if puzzle clues requested for invalid id', async () => {
             mockQuery.mockResolvedValueOnce({ rows: [] });
             const res = await request(app).get('/api/puzzles/999/clues');
             expect(res.statusCode).toBe(404);
        });
    });

    describe('POST /:id/guess', () => {
        const { evaluateGuess } = require('../agents/puzzleAgent');

        it('should evaluate a correct guess', async () => {
            mockQuery.mockResolvedValueOnce({
                rows: [{ id: 1, ticker: 'RELIANCE', company_name: 'Reliance Industries', sector: 'Energy' }]
            });
            evaluateGuess.mockResolvedValue("CORRECT: Spot on!");

            const res = await request(app).post('/api/puzzles/1/guess').send({ guess: 'Reliance' });
            expect(res.statusCode).toBe(200);
            expect(res.body.isCorrect).toBe(true);
            expect(res.body.feedback).toContain("successfully identified");
        });

        it('should evaluate an incorrect guess', async () => {
            mockQuery.mockResolvedValueOnce({
                rows: [{ id: 1, ticker: 'RELIANCE', company_name: 'Reliance Industries', sector: 'Energy' }]
            });
            evaluateGuess.mockResolvedValue("Not quite.");

            const res = await request(app).post('/api/puzzles/1/guess').send({ guess: 'Tata' });
            expect(res.statusCode).toBe(200);
            expect(res.body.isCorrect).toBe(false);
            expect(res.body.feedback).toBe("Not quite.");
        });

        it('should handle missing guess body', async () => {
            const res = await request(app).post('/api/puzzles/1/guess').send({});
            expect(res.statusCode).toBe(400);
        });

        it('should return 404 if puzzle not found for guess', async () => {
            mockQuery.mockResolvedValueOnce({ rows: [] });
            const res = await request(app).post('/api/puzzles/999/guess').send({ guess: 'test' });
            expect(res.statusCode).toBe(404);
        });
    });
});
