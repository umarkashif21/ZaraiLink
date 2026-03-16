import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';

// -------------------------------------------------------------------
// Mock useNavigate
// -------------------------------------------------------------------
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => {
    const actual = jest.requireActual('react-router-dom');
    return { ...actual, useNavigate: () => mockNavigate };
});

import SearchHome from '../SearchHome';

const renderSearchHome = () =>
    render(
        <MemoryRouter>
            <SearchHome />
        </MemoryRouter>
    );

describe('SearchHome Component', () => {
    beforeEach(() => {
        mockNavigate.mockClear();
    });

    test('renders headline/tagline', () => {
        renderSearchHome();
        expect(
            screen.getByText(/what are you looking for today/i)
        ).toBeInTheDocument();
    });

    test('renders search input', () => {
        renderSearchHome();
        const input = screen.getByPlaceholderText(/try/i);
        expect(input).toBeInTheDocument();
        expect(input).toHaveAttribute('type', 'text');
    });

    test('renders search submit button', () => {
        renderSearchHome();
        // The button has text "Search" but also wraps lucide icon — use name match
        expect(
            screen.getByRole('button', { name: /^search$/i })
        ).toBeInTheDocument();
    });

    test('typing in input updates its value', async () => {
        const user = userEvent.setup();
        renderSearchHome();
        const input = screen.getByPlaceholderText(/try/i);
        await user.type(input, 'rice');
        expect(input).toHaveValue('rice');
    });

    test('submitting with non-empty query navigates to /search/results', async () => {
        const user = userEvent.setup();
        renderSearchHome();
        const input = screen.getByPlaceholderText(/try/i);

        await user.type(input, 'wheat suppliers');
        await user.click(screen.getByRole('button', { name: /^search$/i }));

        expect(mockNavigate).toHaveBeenCalledTimes(1);
        const navArg = mockNavigate.mock.calls[0][0];
        expect(navArg).toContain('/search/results');
        expect(navArg).toContain('q=');
        expect(navArg).toContain(encodeURIComponent('wheat suppliers'));
    });

    test('pressing Enter with non-empty query navigates to /search/results', async () => {
        const user = userEvent.setup();
        renderSearchHome();
        const input = screen.getByPlaceholderText(/try/i);

        await user.type(input, 'cotton');
        await user.keyboard('{Enter}');

        expect(mockNavigate).toHaveBeenCalledTimes(1);
        expect(mockNavigate.mock.calls[0][0]).toContain('cotton');
    });

    test('empty query does not navigate', async () => {
        const user = userEvent.setup();
        renderSearchHome();

        await user.click(screen.getByRole('button', { name: /^search$/i }));

        expect(mockNavigate).not.toHaveBeenCalled();
    });

    test('whitespace-only query does not navigate', async () => {
        const user = userEvent.setup();
        renderSearchHome();
        const input = screen.getByPlaceholderText(/try/i);
        await user.type(input, '   ');

        await user.click(screen.getByRole('button', { name: /^search$/i }));

        expect(mockNavigate).not.toHaveBeenCalled();
    });
});
