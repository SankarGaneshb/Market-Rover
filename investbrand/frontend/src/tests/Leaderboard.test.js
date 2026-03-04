import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import Leaderboard from '../pages/Leaderboard';
import { AuthProvider } from '../context/AuthContext';
import axios from 'axios';

jest.mock('axios');
jest.mock('lucide-react', () => ({
    Trophy: () => <div data-testid="trophy-icon">Trophy</div>,
    Share2: () => <div data-testid="share-icon">Share</div>,
    ChevronLeft: () => <div>ChevronLeft</div>,
    ChevronRight: () => <div>ChevronRight</div>,
}));

describe('Leaderboard Component', () => {
    const mockData = {
        data: {
            leaderboard: [
                { id: '1', name: 'Alice', avatar_url: '', score: 1000, streak: 5 },
                { id: '2', name: 'Bob', avatar_url: '', score: 800, streak: 3 },
            ]
        }
    };

    beforeEach(() => {
        axios.get.mockResolvedValue(mockData);
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    const MockApp = () => (
        <BrowserRouter>
            <AuthProvider>
                <Leaderboard />
            </AuthProvider>
        </BrowserRouter>
    );

    it('renders the leaderboard heading', async () => {
        render(<MockApp />);
        expect(await screen.findByRole('heading', { name: /Leaderboard/i })).toBeInTheDocument();
    });

    it('fetches and displays leaderboard data', async () => {
        render(<MockApp />);
        expect(await screen.findByText('Alice')).toBeInTheDocument();
        expect(await screen.findByText('Bob')).toBeInTheDocument();
        expect(screen.getByText('1,000')).toBeInTheDocument();
        expect(screen.getByText('800')).toBeInTheDocument();
    });

    it('switches leaderboard filters', async () => {
        render(<MockApp />);
        const weeklyBtn = await screen.findByText('weekly');
        fireEvent.click(weeklyBtn);
        expect(axios.get).toHaveBeenCalledWith(
            '/api/leaderboard',
            expect.objectContaining({ params: { type: 'weekly' } })
        );
    });
});
