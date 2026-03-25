const { generateUserPersona } = require('../agents/profilerAgent');
const { generateTeacherInsight } = require('../agents/teacherAgent');
const { runQualityCheck } = require('../agents/qcAgent');
const { analyzeError } = require('../agents/opsSupportAgent');
const { getPool } = require('../config/database');

// Mock Database
jest.mock('../config/database', () => ({
  getPool: jest.fn(),
}));

// Mock LangChain
const mockInvoke = jest.fn();
const mockEmbedQuery = jest.fn();

jest.mock('@langchain/google-genai', () => ({
  ChatGoogleGenerativeAI: jest.fn().mockImplementation(() => ({
    invoke: mockInvoke,
  })),
  GoogleGenerativeAIEmbeddings: jest.fn().mockImplementation(() => ({
    embedQuery: mockEmbedQuery,
  })),
}));

// Mock Logger to keep test output clean
jest.mock('../utils/logger', () => ({
  info: jest.fn(),
  error: jest.fn(),
  warn: jest.fn(),
}));

describe('AI Agents Unit Tests', () => {
  let mockQuery;

  beforeEach(() => {
    mockQuery = jest.fn();
    getPool.mockReturnValue({ query: mockQuery });
    process.env.GOOGLE_API_KEY = 'test-key';
    jest.clearAllMocks();
  });

  describe('Profiler Agent', () => {
    it('should generate and save a user persona', async () => {
      mockQuery.mockResolvedValueOnce({
        rows: [{ company_name: 'Reliance', sector: 'Energy', vote_date: new Date(), difficulty: 'easy' }]
      });
      mockInvoke.mockResolvedValueOnce({ content: 'Test Profile Summary' });
      mockEmbedQuery.mockResolvedValueOnce([0.1, 0.2, 0.3]);
      mockQuery.mockResolvedValueOnce({ rows: [] }); // Upsert query

      await generateUserPersona(1);

      expect(mockInvoke).toHaveBeenCalled();
      expect(mockEmbedQuery).toHaveBeenCalledWith('Test Profile Summary');
      expect(mockQuery).toHaveBeenCalledTimes(2);
    });

    it('should skip if no history exists', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] });
      await generateUserPersona(1);
      expect(mockInvoke).not.toHaveBeenCalled();
    });
  });

  describe('Teacher Agent', () => {
    it('should generate a teaser insight', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [{ reading_level: 'beginner' }] });
      mockInvoke.mockResolvedValueOnce({ content: 'Test Insight' });

      const insight = await generateTeacherInsight(1, 'TCS', 'Tata Consultancy');

      expect(insight).toBe('Test Insight');
      expect(mockInvoke).toHaveBeenCalled();
    });
  });

  describe('QC Agent', () => {
    it('should process feedback and disable broken puzzles', async () => {
      mockQuery.mockResolvedValueOnce({
        rows: [
          { puzzle_id: 1, brand_name: 'LogoTest', ticker: 'LT', category: 'logo', rating: 'blurry', count: 5 }
        ]
      });
      mockInvoke.mockResolvedValueOnce({
        content: JSON.stringify({ shouldDisable: true, issueType: 'logo_broken', rationale: 'Too blurry' })
      });
      mockQuery.mockResolvedValueOnce({ rows: [] }); // Update status query

      const result = await runQualityCheck();

      expect(result.success).toBe(true);
      expect(result.actions[0].ticker).toBe('LT');
      expect(result.actions[0].action).toBe('disabled');
    });

    it('should return success even if no feedback', async () => {
      mockQuery.mockResolvedValueOnce({ rows: [] });
      const result = await runQualityCheck();
      expect(result.success).toBe(true);
      expect(result.actions.length).toBe(0);
    });
  });

  describe('Ops Support Agent', () => {
    it('should analyze error and return mitigation', async () => {
      mockInvoke.mockResolvedValueOnce({
        content: JSON.stringify({ rootCause: 'DB Timeout', mitigation: 'Retry', severity: 'high' })
      });

      const analysis = await analyzeError(new Error('Test Error'), { method: 'GET', path: '/test', body: {} });

      expect(analysis.rootCause).toBe('DB Timeout');
      expect(mockInvoke).toHaveBeenCalled();
    });
  });
});
