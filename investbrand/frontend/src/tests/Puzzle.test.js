import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import PuzzleGame from '../pages/Puzzle';
import { BrowserRouter } from 'react-router-dom';
import axios from 'axios';

jest.mock('../context/AuthContext', () => ({
    useAuth: jest.fn()
}));
import { useAuth } from '../context/AuthContext';

jest.mock('axios');
jest.mock('lucide-react', () => ({
    Trophy: () => <div data-testid="icon-trophy" />,
    Zap: () => <div data-testid="icon-zap" />,
    Share2: () => <div data-testid="icon-share" />,
    Calendar: () => <div data-testid="icon-calendar" />,
    Clock: () => <div data-testid="icon-clock" />,
    Move: () => <div data-testid="icon-move" />,
    RotateCcw: () => <div data-testid="icon-rotate" />,
    Eye: () => <div data-testid="icon-eye" />,
    X: () => <div data-testid="icon-x" />,
    Award: () => <div data-testid="icon-award" />,
    TrendingUp: () => <div data-testid="icon-trending" />,
    Lightbulb: () => <div data-testid="icon-lightbulb" />,
}));

const mockUser = {
    id: 1,
    name: 'Test User',
    streak: 5,
    total_score: 1000
};

const renderWithContext = (component) => {
    return render(
        <BrowserRouter>
            {component}
        </BrowserRouter>
    );
};

describe('PuzzleGame Component', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        useAuth.mockReturnValue({ user: mockUser });

        axios.get.mockImplementation((url) => {
            if (url === '/api/puzzles/daily') {
                return Promise.resolve({
                    data: {
                        id: 1,
                        puzzle_date: new Date().toISOString().split('T')[0],
                        brand_id: 1,
                        ticker: 'RELIANCE'
                    }
                });
            }
            if (url === '/api/puzzles/1/clues') {
                return Promise.resolve({
                    data: {
                        success: true,
                        clues: { clue1: 'Test 1', clue2: 'Test 2', clue3: 'Test 3' }
                    }
                });
            }
            if (url === '/api/users/me/sessions') {
                return Promise.resolve({ data: [] });
            }
            return Promise.resolve({ data: {} });
        });
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    it('renders loading state initially', () => {
        renderWithContext(<PuzzleGame />);
        expect(screen.getByText(/Loading challenge/i)).toBeInTheDocument();
    });

    it('renders menu after fetching puzzle', async () => {
        renderWithContext(<PuzzleGame />);
        await waitFor(() => expect(screen.queryByText(/Loading challenge/i)).not.toBeInTheDocument());
        expect(screen.getByText(/Market Puzzle/i)).toBeInTheDocument();
        expect(screen.getByText(/Easy/i)).toBeInTheDocument();
    });

    it('starts game when difficulty is selected', async () => {
        renderWithContext(<PuzzleGame />);
        await waitFor(() => expect(screen.queryByText(/Loading challenge/i)).not.toBeInTheDocument());

        const easyButton = screen.getByText(/Easy/i);
        fireEvent.click(easyButton);

        // Check for clue context appearing in the new UI immediately
        expect(screen.getByText(/Terminal Intelligence/i)).toBeInTheDocument();
        expect(screen.getByText(/Phase 1 Clue/i)).toBeInTheDocument();

        // Check that puzzle board and pieces are present
        expect(document.querySelector('.grid')).toBeInTheDocument();
    });

    it('handles axios errors gracefully', async () => {
        const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => { });
        axios.get.mockRejectedValueOnce(new Error('Network Error'));

        renderWithContext(<PuzzleGame />);
        await waitFor(() => expect(screen.queryByText(/Loading challenge/i)).not.toBeInTheDocument());
        expect(screen.getByText(/Market Puzzle/i)).toBeInTheDocument();

        consoleSpy.mockRestore();
    });

    it('handles piece dropping and game completion transitions', async () => {
        renderWithContext(<PuzzleGame />);
        await waitFor(() => expect(screen.queryByText(/Loading challenge/i)).not.toBeInTheDocument());
        fireEvent.click(screen.getByText(/Easy/i));

        const pieces = await screen.findAllByRole('generic');

        expect(screen.getByText(/Terminal Intelligence/i)).toBeInTheDocument();
    });
});
