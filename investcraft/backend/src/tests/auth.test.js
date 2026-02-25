jest.mock('../config/database', () => ({
    getPool: jest.fn(),
    initializePool: jest.fn().mockResolvedValue()
}));

const mockVerifyIdToken = jest.fn();

jest.mock('google-auth-library', () => {
    return {
        OAuth2Client: jest.fn().mockImplementation(() => {
            return {
                verifyIdToken: mockVerifyIdToken
            }
        })
    }
});

const request = require('supertest');
const express = require('express');
const { getPool } = require('../config/database');
const { OAuth2Client } = require('google-auth-library');
const authRoutes = require('../routes/auth');
const jwt = require('jsonwebtoken');

const app = express();
app.use(express.json());
app.use('/api/auth', authRoutes);

describe('Auth Routes', () => {
    let mockQuery;

    beforeEach(() => {
        mockQuery = jest.fn();
        getPool.mockReturnValue({ query: mockQuery });
        process.env.JWT_SECRET = 'test-secret';
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    it('should return 400 if google token is missing', async () => {
        const res = await request(app).post('/api/auth/google').send({});
        expect(res.statusCode).toBe(400);
        expect(res.body.error).toBe('Google token required');
    });

    it('should authenticate user and return jwt token', async () => {
        const mockTicket = {
            getPayload: () => ({ sub: '123', email: 'test@test.com', name: 'Test User', picture: 'pic.jpg' })
        };
        mockVerifyIdToken.mockResolvedValue(mockTicket);

        const mockDbUser = {
            id: 1, name: 'Test User', email: 'test@test.com', avatar_url: 'pic.jpg', streak: 0, total_score: 0
        };
        mockQuery.mockResolvedValue({ rows: [mockDbUser] });

        const res = await request(app).post('/api/auth/google').send({ token: 'valid-token' });
        expect(res.statusCode).toBe(200);
        expect(res.body.token).toBeDefined();
        expect(res.body.user.email).toBe('test@test.com');
    });

    it('should handle invalid google token gracefully', async () => {
        mockVerifyIdToken.mockRejectedValue(new Error('Invalid token'));

        const res = await request(app).post('/api/auth/google').send({ token: 'invalid-token' });
        expect(res.statusCode).toBe(401);
        expect(res.body.error).toBe('Authentication failed');
    });

    it('should return 401 on /me if no token provided', async () => {
        const res = await request(app).get('/api/auth/me');
        expect(res.statusCode).toBe(401);
    });

    it('should return user data on /me if valid token provided', async () => {
        const token = jwt.sign({ userId: 1, email: 'test@test.com' }, process.env.JWT_SECRET);
        const mockDbUser = {
            id: 1, name: 'Test User', email: 'test@test.com', avatar_url: 'pic.jpg', streak: 0, total_score: 0
        };
        mockQuery.mockResolvedValue({ rows: [mockDbUser] });

        const res = await request(app)
            .get('/api/auth/me')
            .set('Authorization', `Bearer ${token}`);

        expect(res.statusCode).toBe(200);
        expect(res.body.user.name).toBe('Test User');
    });

    it('should return 401 on /me if user not found in db', async () => {
        const token = jwt.sign({ userId: 1, email: 'test@test.com' }, process.env.JWT_SECRET);
        mockQuery.mockResolvedValue({ rows: [] });

        const res = await request(app)
            .get('/api/auth/me')
            .set('Authorization', `Bearer ${token}`);

        expect(res.statusCode).toBe(401);
    });
});
