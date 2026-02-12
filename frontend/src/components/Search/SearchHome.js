import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search } from 'lucide-react';

const SearchHome = () => {
    const [query, setQuery] = useState('');
    const navigate = useNavigate();

    const handleSearch = (e) => {
        e.preventDefault();
        if (query.trim()) {
            navigate(`/search/results?q=${encodeURIComponent(query)}`);
        }
    };

    const handlePillClick = (text) => {
        setQuery(text);
        // Optional: auto-search or just set text
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
            <div className="max-w-3xl w-full text-center space-y-8">

                {/* Hero Text */}
                <h1 className="text-4xl md:text-5xl font-bold text-gray-900 tracking-tight">
                    What are you looking for today?
                </h1>

                {/* Search Bar */}
                <form onSubmit={handleSearch} className="relative w-full max-w-2xl mx-auto">
                    <div className="relative group">
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Try 'Import Dextrose Anhydrous from China under $700'..."
                            className="w-full h-14 pl-14 pr-4 rounded-full border-2 border-gray-200 shadow-sm focus:border-indigo-500 focus:ring-0 text-lg transition-all"
                        />
                        <div className="absolute left-5 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-indigo-500 transition-colors">
                            <Search size={24} />
                        </div>
                        <button
                            type="submit"
                            className="absolute right-2 top-2 bottom-2 px-6 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full font-medium transition-colors"
                        >
                            Search
                        </button>
                    </div>
                </form>

                {/* Intent Pills */}
                <div className="flex flex-wrap justify-center gap-3">
                    {['I want to buy', 'I want to sell', 'Find suppliers', 'Find buyers'].map((pill) => (
                        <button
                            key={pill}
                            onClick={() => handlePillClick(pill)}
                            className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm font-medium text-gray-600 hover:border-indigo-500 hover:text-indigo-600 transition-colors shadow-sm"
                        >
                            {pill}
                        </button>
                    ))}
                </div>

                {/* Recent / Examples (Placeholder) */}
                <div className="pt-12 text-gray-500 text-sm">
                    <p className="mb-4 font-medium uppercase tracking-wide">Example Queries</p>
                    <div className="flex flex-wrap justify-center gap-4 text-gray-400">
                        <span>"Dextrose suppliers in Pakistan"</span>
                        <span>•</span>
                        <span>"Buy Urea 46%"</span>
                        <span>•</span>
                        <span>"Who sells PVC Resin?"</span>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default SearchHome;
