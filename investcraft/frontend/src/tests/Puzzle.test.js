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

describe('Puzzle Component', () => {
    beforeEach(() => {
        useAuth.mockReturnValue({ user: mockUser });
        axios.get.mockImplementation((url) => {
            if (url === '/api/puzzles/daily') {
                return Promise.resolve({ data: { id: 1, ticker: 'RELIANCE' } });
            }
            if (url === '/api/users/me/sessions') {
                return Promise.resolve({ data: [] });
            }
            return Promise.reject(new Error('not found'));
        });
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    it('renders loading state initially', () => {
        renderWithContext(<PuzzleGame />);
        expect(screen.getByText(/Loading daily challenge/i)).toBeInTheDocument();
    });

    it('renders menu after fetching puzzle', async () => {
        renderWithContext(<PuzzleGame />);
        await waitFor(() => expect(screen.queryByText(/Loading daily challenge/i)).not.toBeInTheDocument());
        expect(screen.getByText(/Brand to Stock/i)).toBeInTheDocument();
        expect(screen.getByText(/Choose Difficulty/i)).toBeInTheDocument();
    });

    it('starts game when difficulty is selected', async () => {
        renderWithContext(<PuzzleGame />);
        await waitFor(() => expect(screen.queryByText(/Loading daily challenge/i)).not.toBeInTheDocument());

        const easyButton = screen.getByText(/Easy/i);
        fireEvent.click(easyButton);

        expect(screen.getByText(/Solve It!/i)).toBeInTheDocument();
        expect(screen.getByText(/Progress:/i)).toBeInTheDocument();
    });

    it('shows hint when hint button is clicked', async () => {
        renderWithContext(<PuzzleGame />);
        await waitFor(() => expect(screen.queryByText(/Loading daily challenge/i)).not.toBeInTheDocument());
        fireEvent.click(screen.getByText(/Easy/i));

        const hintButton = screen.getByText(/Hint/i);
        fireEvent.click(hintButton);

        expect(screen.getByAltText(/Hint/i)).toBeInTheDocument();
    });

    it('handles axios errors gracefully', async () => {
        axios.get.mockRejectedValueOnce(new Error('Network Error'));
        renderWithContext(<PuzzleGame />);
        await waitFor(() => expect(screen.queryByText(/Loading daily challenge/i)).not.toBeInTheDocument());
        expect(screen.getByText(/Brand to Stock/i)).toBeInTheDocument();
    });
});
