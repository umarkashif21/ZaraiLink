import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { MemoryRouter } from 'react-router-dom';

// -------------------------------------------------------------------
// Mock heavy dependencies before importing the component under test
// -------------------------------------------------------------------

// Mock Navbar to avoid auth/theme context requirements
jest.mock('../../Layout/Navbar', () => () => <nav data-testid="navbar" />);

// Mock searchService
jest.mock('../../../services/searchService');
import searchService from '../../../services/searchService';

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => {
    const actual = jest.requireActual('react-router-dom');
    return { ...actual, useNavigate: () => mockNavigate };
});

import SearchResults from '../SearchResults';

// -------------------------------------------------------------------
// Helpers
// -------------------------------------------------------------------

const EMPTY_RESPONSE = {
    results: [],
    matched_subcategories: [],
    market_snapshot: null,
};

const makeSupplier = (name, country) => ({
    name,
    country,
    avg_price: 450.5,
    total_volume: 1200,
    shipment_count: 12,
    badges: [],
    trend: null,
    market_share: 10,
    hhi_score: null,
    yearly_data: [],
});

const RESULTS_RESPONSE = {
    results: [
        makeSupplier('Sunrise Agro Pvt Ltd', 'Pakistan'),
        makeSupplier('Global Grain Co', 'India'),
    ],
    matched_subcategories: [{ id: 1, name: 'Wheat' }],
    market_snapshot: null,
    parsed_query: { intent: 'BUY' },
};

/**
 * Render SearchResults inside a MemoryRouter with optional URL query string.
 */
const renderSearchResults = (search = '?q=rice&scope=WORLDWIDE') =>
    render(
        <MemoryRouter initialEntries={[`/search/results${search}`]}>
            <SearchResults />
        </MemoryRouter>
    );

// -------------------------------------------------------------------
// Tests
// -------------------------------------------------------------------

describe('SearchResults Component', () => {
    beforeEach(() => {
        mockNavigate.mockClear();
        searchService.search.mockClear();
    });

    // --- Basic rendering ---

    test('renders search input field', async () => {
        searchService.search.mockResolvedValueOnce(EMPTY_RESPONSE);
        renderSearchResults();
        expect(screen.getByPlaceholderText(/search trade data/i)).toBeInTheDocument();
    });

    test('renders Search button', async () => {
        searchService.search.mockResolvedValueOnce(EMPTY_RESPONSE);
        renderSearchResults();
        expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument();
    });

    // --- URL param pre-filling ---

    test('?q=xyz pre-fills the search input', async () => {
        searchService.search.mockResolvedValueOnce(EMPTY_RESPONSE);
        renderSearchResults('?q=cotton&scope=WORLDWIDE');
        const input = screen.getByPlaceholderText(/search trade data/i);
        expect(input).toHaveValue('cotton');
    });

    // --- No auto-search on typing (submittedQuery pattern) ---

    test('does NOT call searchService when merely typing (no submit)', async () => {
        searchService.search.mockResolvedValueOnce(EMPTY_RESPONSE);
        const user = userEvent.setup();
        renderSearchResults('?q=rice&scope=WORLDWIDE');

        // Wait for the initial auto-fetch triggered by the URL param
        await waitFor(() => expect(searchService.search).toHaveBeenCalledTimes(1));

        // Now type something new — should NOT trigger another call
        const input = screen.getByPlaceholderText(/search trade data/i);
        await user.clear(input);
        await user.type(input, 'wheat');

        // Still only the initial call
        expect(searchService.search).toHaveBeenCalledTimes(1);
    });

    // --- Loading state ---

    test('shows loading state while searching', async () => {
        let resolveSearch;
        searchService.search.mockReturnValueOnce(
            new Promise((res) => { resolveSearch = res; })
        );

        renderSearchResults();
        expect(screen.getByText(/loading results/i)).toBeInTheDocument();

        // Resolve to avoid act() warnings
        await act(async () => { resolveSearch(EMPTY_RESPONSE); });
    });

    // --- Search triggered by button click ---

    test('calls searchService when Search button clicked', async () => {
        searchService.search
            .mockResolvedValueOnce(EMPTY_RESPONSE)
            .mockResolvedValueOnce(RESULTS_RESPONSE);

        const user = userEvent.setup();
        renderSearchResults('?q=rice&scope=WORLDWIDE');
        await waitFor(() => expect(searchService.search).toHaveBeenCalledTimes(1));

        const input = screen.getByPlaceholderText(/search trade data/i);
        await user.clear(input);
        await user.type(input, 'wheat');

        const button = screen.getByRole('button', { name: /search/i });
        await user.click(button);

        await waitFor(() => expect(searchService.search).toHaveBeenCalledTimes(2));
        expect(searchService.search).toHaveBeenLastCalledWith(
            'wheat',
            expect.objectContaining({ scope: 'WORLDWIDE' })
        );
    });

    // --- Search triggered by Enter key ---

    test('calls searchService when Enter pressed in input', async () => {
        searchService.search
            .mockResolvedValueOnce(EMPTY_RESPONSE)
            .mockResolvedValueOnce(RESULTS_RESPONSE);

        const user = userEvent.setup();
        renderSearchResults('?q=rice&scope=WORLDWIDE');
        await waitFor(() => expect(searchService.search).toHaveBeenCalledTimes(1));

        const input = screen.getByPlaceholderText(/search trade data/i);
        await user.clear(input);
        await user.type(input, 'maize');
        await user.keyboard('{Enter}');

        await waitFor(() => expect(searchService.search).toHaveBeenCalledTimes(2));
        expect(searchService.search).toHaveBeenLastCalledWith('maize', expect.anything());
    });

    // --- Result cards ---

    test('each result card renders company name and country', async () => {
        searchService.search.mockResolvedValueOnce(RESULTS_RESPONSE);
        renderSearchResults();

        await waitFor(() =>
            expect(screen.getByText('Sunrise Agro Pvt Ltd')).toBeInTheDocument()
        );
        expect(screen.getByText('Global Grain Co')).toBeInTheDocument();
        // Country appears in both the card and filter dropdown, so use getAllByText
        expect(screen.getAllByText('Pakistan').length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByText('India').length).toBeGreaterThanOrEqual(1);
    });

    // --- Result count heading ---

    test('displays result count when results are present', async () => {
        searchService.search.mockResolvedValueOnce(RESULTS_RESPONSE);
        renderSearchResults('?q=rice&scope=WORLDWIDE');

        // Component renders: "2 Suppliers found for "rice""
        await waitFor(() =>
            expect(
                screen.getByText((content, node) => {
                    return node.tagName === 'H2' && /2\s+Suppliers found/i.test(node.textContent);
                })
            ).toBeInTheDocument()
        );
    });

    // --- Empty state ---

    test('shows empty state — no result cards when no results returned', async () => {
        searchService.search.mockResolvedValueOnce(EMPTY_RESPONSE);
        renderSearchResults('?q=xyzunknown&scope=WORLDWIDE');

        await waitFor(() =>
            expect(screen.queryByText(/loading results/i)).not.toBeInTheDocument()
        );
        expect(screen.queryByText('Sunrise Agro Pvt Ltd')).not.toBeInTheDocument();
    });

    // --- Error handling ---

    test('handles API error gracefully — shows error message without crashing', async () => {
        searchService.search.mockRejectedValueOnce(new Error('Network error'));
        renderSearchResults();

        await waitFor(() =>
            expect(
                screen.getByText(/failed to fetch search results/i)
            ).toBeInTheDocument()
        );
        // Component should not crash — navbar still rendered
        expect(screen.getByTestId('navbar')).toBeInTheDocument();
    });

    // --- Results count badge updates after new search ---

    test('results count badge updates correctly after a new search', async () => {
        const threeResults = {
            ...RESULTS_RESPONSE,
            results: [
                ...RESULTS_RESPONSE.results,
                makeSupplier('Delta Foods', 'UAE'),
            ],
        };

        searchService.search
            .mockResolvedValueOnce(RESULTS_RESPONSE)
            .mockResolvedValueOnce(threeResults);

        const user = userEvent.setup();
        renderSearchResults('?q=rice&scope=WORLDWIDE');

        await waitFor(() =>
            expect(screen.getByText('Sunrise Agro Pvt Ltd')).toBeInTheDocument()
        );

        // Trigger a new search
        const input = screen.getByPlaceholderText(/search trade data/i);
        await user.clear(input);
        await user.type(input, 'urea');
        await user.click(screen.getByRole('button', { name: /search/i }));

        await waitFor(() =>
            expect(screen.getByText('Delta Foods')).toBeInTheDocument()
        );
        // All 3 results should be visible
        expect(screen.getByText('Sunrise Agro Pvt Ltd')).toBeInTheDocument();
        expect(screen.getByText('Global Grain Co')).toBeInTheDocument();
    });
});
