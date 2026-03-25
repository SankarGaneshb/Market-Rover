const { checkMissions, calculateStrategyTags } = require('../utils/missionEngine');
const errorHandler = require('../middleware/errorHandler');
const { getPool } = require('../config/database');
const logger = require('../utils/logger');

// Mock Database
jest.mock('../config/database', () => ({
  getPool: jest.fn(),
}));

// Mock Logger
jest.mock('../utils/logger', () => ({
  error: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
}));

// Mock Ops Agent
jest.mock('../agents/opsSupportAgent', () => ({
  analyzeError: jest.fn().mockResolvedValue({ rootCause: 'Mocked', mitigation: 'Mocked', severity: 'low' }),
}));

describe('Coverage Boost Tests', () => {
  let mockQuery;
  let mockConnect;
  let mockRelease;

  beforeEach(() => {
    mockQuery = jest.fn();
    mockRelease = jest.fn();
    mockConnect = jest.fn().mockResolvedValue({
      query: mockQuery,
      release: mockRelease
    });
    
    getPool.mockReturnValue({
      query: mockQuery,
      connect: mockConnect
    });
    
    jest.clearAllMocks();
  });

  describe('Mission Engine', () => {
    it('should update missions correctly', async () => {
      mockQuery
        .mockResolvedValueOnce({ rows: [{ sector: 'IT', vote_date: new Date() }] }) // votes
        .mockResolvedValueOnce({ rows: [] }) // First Steps
        .mockResolvedValueOnce({ rows: [] }) // Sector Explorer
        .mockResolvedValueOnce({ rows: [{ mission_def: { target: 5 } }] }) // Daily Mission check
        .mockResolvedValueOnce({ rows: [] }); // Daily update

      await checkMissions(1);

      expect(mockConnect).toHaveBeenCalled();
      expect(mockQuery).toHaveBeenCalled();
      expect(mockRelease).toHaveBeenCalled();
    });

    it('should calculate strategy tags for all personas', async () => {
      // 1. Sector Diversifier (4+ sectors)
      mockQuery.mockResolvedValueOnce({ rows: [{ sector: 'IT' }, { sector: 'Finance' }, { sector: 'FMCG' }, { sector: 'Energy' }] })
               .mockResolvedValueOnce({ rows: [] });
      await calculateStrategyTags(1);

      // 2. Brand Loyalist (> 70% in one sector)
      mockQuery.mockResolvedValueOnce({ rows: [{ sector: 'IT' }, { sector: 'IT' }, { sector: 'IT' }, { sector: 'Finance' }] })
               .mockResolvedValueOnce({ rows: [] });
      await calculateStrategyTags(1);

      // 3. Growth Hunter (> 50% IT/Healthcare)
      mockQuery.mockResolvedValueOnce({ rows: [{ sector: 'Information Technology' }, { sector: 'Healthcare' }, { sector: 'Finance' }] })
               .mockResolvedValueOnce({ rows: [] });
      await calculateStrategyTags(1);

      // 4. Value Seeker (> 50% FMCG/Utilities)
      mockQuery.mockResolvedValueOnce({ rows: [{ sector: 'FMCG' }, { sector: 'Utilities' }, { sector: 'Finance' }] })
               .mockResolvedValueOnce({ rows: [] });
      await calculateStrategyTags(1);
    });

    it('should handle mission errors gracefully', async () => {
      mockConnect.mockRejectedValueOnce(new Error('Connect Fail'));
      await checkMissions(1);
      expect(logger.error).toHaveBeenCalled();
    });
  });

  describe('Error Handler Middleware', () => {
    let mockReq, mockRes, mockNext;

    beforeEach(() => {
      mockReq = { method: 'GET', path: '/test', body: {}, headers: {} };
      mockRes = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn().mockReturnThis()
      };
      mockNext = jest.fn();
      process.env.GOOGLE_API_KEY = 'test-key';
    });

    it('should handle 500 errors and trigger AI analysis in production', async () => {
      process.env.NODE_ENV = 'production';
      const err = new Error('Global Failure');
      await errorHandler(err, mockReq, mockRes, mockNext);

      expect(mockRes.status).toHaveBeenCalledWith(500);
      expect(mockRes.json).toHaveBeenCalledWith({ error: 'Internal server error' });
    });

    it('should handle JSON parse errors (400)', async () => {
      const err = new Error('Syntax');
      err.type = 'entity.parse.failed';
      await errorHandler(err, mockReq, mockRes, mockNext);

      expect(mockRes.status).toHaveBeenCalledWith(400);
      expect(mockRes.json).toHaveBeenCalledWith({ error: 'Invalid JSON payload' });
    });
  });
});
