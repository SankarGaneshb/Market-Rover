import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import GlitterBadge from '../components/GlitterBadge';

describe('GlitterBadge Component', () => {
    const mockLevelConfig = {
        name: 'Master',
        icon: '🏆',
        bg: 'bg-blue-500',
        accent: '#3b82f6',
        color: 'text-blue-500',
        minDays: 0
    };

    it('renders with standard sizes', () => {
        const { container } = render(<GlitterBadge name="Star" levelConfig={mockLevelConfig} size="normal" />);
        expect(container.querySelector('svg')).toBeInTheDocument();
        expect(screen.getByText('Star')).toBeInTheDocument();
    });

    it('renders with small size correctly', () => {
        const { container } = render(<GlitterBadge name="Small Star" levelConfig={mockLevelConfig} size="small" />);
        expect(container.querySelector('svg')).toBeInTheDocument();
        // Name is only rendered for normal/large sizes, small just shows the badge
        expect(screen.queryByText('Small Star')).not.toBeInTheDocument();
    });

    it('applies level config colors', () => {
        const { container } = render(<GlitterBadge name="Fire" levelConfig={mockLevelConfig} size="normal" />);
        // Ensure the background class from the config is applied
        const element = container.querySelector('.bg-blue-500');
        expect(element).toBeInTheDocument();
    });

    it('renders empty sparkle elements for animation', () => {
        const { container } = render(<GlitterBadge name="Sparkle" levelConfig={mockLevelConfig} size="normal" />);
        // The component renders standard pseudo-elements or empty divs for the glitter effect
        const sparkles = container.querySelectorAll('.absolute');
        expect(sparkles.length).toBeGreaterThan(0);
    });
});
