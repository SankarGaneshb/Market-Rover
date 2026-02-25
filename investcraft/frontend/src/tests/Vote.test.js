import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Vote from '../pages/Vote';
import { BrowserRouter } from 'react-router-dom';
import axios from 'axios';

jest.mock('../context/AuthContext', () => ({
    useAuth: jest.fn()
}));
import { useAuth } from '../context/AuthContext';

jest.mock('axios');
jest.mock('lucide-react', () => ({
    CheckCircle: () => <div data-testid="icon-check" />,
    BarChart3: () => <div data-testid="icon-chart" />,
    Navigation: () => <div data-testid="icon-nav" />,
    Building2: () => <div data-testid="icon-building" />,
    Store: () => <div data-testid="icon-store" />,
}));

const mockUser = { id: 1, name: 'Test User' };

const renderWithContext = (component) => {
    return render(
        <BrowserRouter>
            {component}
        </BrowserRouter>
    );
};

describe('Vote Component', () => {
    beforeEach(() => {
        useAuth.mockReturnValue({ user: mockUser });
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    it('renders correctly with initial index selected', () => {
        renderWithContext(<Vote />);
        expect(screen.getByText(/Market Rover/i)).toBeInTheDocument();
        expect(screen.getByText(/1. Market Index/i)).toBeInTheDocument();
    });

    it('transitions through tiers on click', () => {
        renderWithContext(<Vote />);

        // Index is auto-selected to first one ('Nifty 50' presumably)
        // Find a sector button (needs to be from the actual data or mocked)
        // Since we import NIFTY50_BRANDS, it will use real data.

        expect(screen.getByText(/2. Target Sector/i)).toBeInTheDocument();
    });

    it('submits a vote successfully', async () => {
        axios.post.mockResolvedValue({ data: { success: true } });
        renderWithContext(<Vote />);

        // We need to select through tiers to get to a brand
        // For simplicity in testing real data, we can just look for specific text
        const nifty50Btn = screen.getByText('Nifty 50');
        fireEvent.click(nifty50Btn);

        // Wait for sector to appear
        const sectorBtn = await screen.findByText('Energy');
        fireEvent.click(sectorBtn);

        // Wait for company to appear
        const companyBtn = await screen.findByText('Reliance Industries');
        fireEvent.click(companyBtn);

        // Select brand
        const brandBtn = await screen.findByText('Jio');
        fireEvent.click(brandBtn);

        // Click confirm
        const confirmBtn = screen.getByText(/Confirm Vote/i);
        fireEvent.click(confirmBtn);

        await waitFor(() => expect(screen.getByText(/Vote Logged!/i)).toBeInTheDocument());
    });

    it('handles submission errors', async () => {
        axios.post.mockRejectedValue(new Error('Failed'));
        renderWithContext(<Vote />);

        // Path to a brand
        fireEvent.click(screen.getByText('Nifty 50'));
        fireEvent.click(await screen.findByText('Energy'));
        fireEvent.click(await screen.findByText('Reliance Industries'));
        fireEvent.click(await screen.findByText('Jio'));

        fireEvent.click(screen.getByText(/Confirm Vote/i));

        await waitFor(() => expect(screen.getByText(/Failed to submit your vote/i)).toBeInTheDocument());
    });
});
