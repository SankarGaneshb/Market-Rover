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
const userRoutes = require('../routes/users');

const app = express();
app.use(express.json());
app.use('/api/users', userRoutes);

describe('Users Routes', () => {
    let mockQuery;

    beforeEach(() => {
        mockQuery = jest.fn();
        getPool.mockReturnValue({ query: mockQuery });
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    it('should fetch user profile on /me', async () => {
        const mockDbUser = {
            id: 1, name: 'Test User', email: 'test@example.com', avatar_url: 'pic.jpg',
            streak: 5, total_score: 100, puzzles_completed: '10', created_at: '2023-01-01'
        };
        mockQuery.mockResolvedValue({ rows: [mockDbUser] });

        const res = await request(app).get('/api/users/me');
        expect(res.statusCode).toBe(200);
        expect(res.body.name).toBe('Test User');
        expect(res.body.puzzlesCompleted).toBe(10);
    });

    it('should handle db errors on /me', async () => {
        mockQuery.mockRejectedValue(new Error('DB Error'));

        const res = await request(app).get('/api/users/me');
        expect(res.statusCode).toBe(500);
        expect(res.body.error).toBe('Failed to fetch profile');
    });

    it('should fetch user sessions on /me/sessions', async () => {
        const mockSessions = [
            { puzzle_id: 1, completed: true, score: 50, created_at: '2023-01-01' },
            { puzzle_id: 2, completed: true, score: 60, created_at: '2023-01-02' }
        ];
        mockQuery.mockResolvedValue({ rows: mockSessions });

        const res = await request(app).get('/api/users/me/sessions');
        expect(res.statusCode).toBe(200);
        expect(res.body).toHaveLength(2);
        expect(res.body[0].score).toBe(50);
    });

    it('should handle db errors on /me/sessions', async () => {
        mockQuery.mockRejectedValue(new Error('DB Error'));

        const res = await request(app).get('/api/users/me/sessions');
        expect(res.statusCode).toBe(500);
        expect(res.body.error).toBe('Failed to fetch sessions');
    });
});
