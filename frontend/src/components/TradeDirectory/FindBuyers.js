import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Search, SlidersHorizontal, X, Building2, MapPin, Tag } from 'lucide-react';
import Navbar from '../Layout/Navbar';
import WatchlistButton from '../Common/WatchlistButton';
import Pagination from '../Common/Pagination';
import useWatchlist from '../../hooks/useWatchlist';
import useDebounce from '../../hooks/useDebounce';

const API = process.env.REACT_APP_API_BASE_URL;

const FindBuyers = () => {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [buyerRoleId, setBuyerRoleId] = useState(null);

  const [search, setSearch] = useState('');
  const [country, setCountry] = useState('');
  const [sector, setSector] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  const [currentPage, setCurrentPage] = useState(1);
  const [sortBy, setSortBy] = useState('name_asc');
  const itemsPerPage = 12;

  const [filterOptions, setFilterOptions] = useState({ countries: [], sectors: [] });
  const { isInWatchlist, toggleWatchlist } = useWatchlist();
  const debouncedSearch = useDebounce(search, 300);

  useEffect(() => {
    const init = async () => {
      try {
        const [secRes, rolesRes] = await Promise.all([
          fetch(`${API}/api/sectors/`),
          fetch(`${API}/api/company-roles/`),
        ]);
        let resolvedRoleId = null;
        if (secRes.ok) {
          const d = await secRes.json();
          setFilterOptions(prev => ({ ...prev, sectors: d }));
        }
        if (rolesRes.ok) {
          const roles = await rolesRes.json();
          const r = roles.find(r => r.name.toLowerCase() === 'buyer') || roles.find(r => r.name.toLowerCase() === 'buyers');
          if (r) {
            setBuyerRoleId(r.id);
            resolvedRoleId = r.id;
          }
        }
        if (resolvedRoleId) {
          const cRes = await fetch(`${API}/api/companies/countries/?role=${resolvedRoleId}`);
          if (cRes.ok) {
            const d = await cRes.json();
            setFilterOptions(prev => ({ ...prev, countries: d }));
          }
        }
      } catch (e) { console.error(e); }
    };
    init();
  }, []);

  const fetchCompanies = useCallback(async () => {
    if (!buyerRoleId) return;
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ role: buyerRoleId });
      if (debouncedSearch) params.append('search', debouncedSearch);
      if (country) params.append('country', country);
      if (sector) params.append('sector', sector);
      const res = await fetch(`${API}/api/companies/?${params}`, { credentials: 'include' });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setCompanies(data.results || data);
      setCurrentPage(1);
    } catch {
      setError('Failed to load buyers. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [buyerRoleId, debouncedSearch, country, sector]);

  useEffect(() => { fetchCompanies(); }, [fetchCompanies]);

  const reset = () => { setSearch(''); setCountry(''); setSector(''); };
  const activeFilterCount = [search, country, sector].filter(Boolean).length;

  const sorted = useMemo(() => {
    const arr = [...companies];
    const dir = sortBy.endsWith('asc') ? 1 : -1;
    return arr.sort((a, b) => (a.name || '').localeCompare(b.name || '') * dir);
  }, [companies, sortBy]);

  const totalPages = Math.ceil(sorted.length / itemsPerPage);
  const paginated = sorted.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  return (
    <div className="min-h-screen bg-slate-50 font-sans">
      <Navbar />

      <div className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-6 py-10">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-blue-600 mb-1">Trade Directory</p>
              <h1 className="text-3xl font-black text-slate-900 tracking-tight">Find Buyers</h1>
              <p className="text-slate-500 mt-1">Connect with verified buyers and distributors from Pakistan's supply chain.</p>
            </div>
            <div className="flex gap-2">
              <Link to="/trade-directory/find-suppliers"
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-600 font-semibold rounded-xl text-sm transition-colors">
                Switch to Suppliers →
              </Link>
            </div>
          </div>

          <div className="mt-6 flex gap-3">
            <div className="relative flex-1">
              <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Search by company name…"
                className="w-full h-12 pl-11 pr-4 bg-white border border-slate-200 rounded-xl text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 transition-all"
              />
              {search && (
                <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                  <X size={16} />
                </button>
              )}
            </div>
            <button
              onClick={() => setShowFilters(p => !p)}
              className={`flex items-center gap-2 px-4 h-12 rounded-xl font-semibold text-sm border transition-all ${showFilters || activeFilterCount > 0
                  ? 'bg-blue-500 text-white border-blue-500 shadow-lg shadow-blue-500/20'
                  : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
                }`}
            >
              <SlidersHorizontal size={16} />
              Filters
              {activeFilterCount > 0 && (
                <span className="bg-white/30 text-white text-xs font-bold px-1.5 py-0.5 rounded-full">{activeFilterCount}</span>
              )}
            </button>
          </div>

          {showFilters && (
            <div className="mt-4 p-4 bg-slate-50 border border-slate-200 rounded-2xl flex flex-wrap gap-4 items-end">
              <div className="flex flex-col gap-1">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Country</label>
                <select value={country} onChange={e => setCountry(e.target.value)}
                  className="h-10 px-3 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none focus:border-blue-500 min-w-[160px]">
                  <option value="">All Countries</option>
                  {filterOptions.countries.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Sector</label>
                <select value={sector} onChange={e => setSector(e.target.value)}
                  className="h-10 px-3 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none focus:border-blue-500 min-w-[160px]">
                  <option value="">All Sectors</option>
                  {filterOptions.sectors.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">Sort</label>
                <select value={sortBy} onChange={e => setSortBy(e.target.value)}
                  className="h-10 px-3 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none focus:border-blue-500">
                  <option value="name_asc">Name A–Z</option>
                  <option value="name_desc">Name Z–A</option>
                </select>
              </div>
              {activeFilterCount > 0 && (
                <button onClick={reset}
                  className="h-10 px-4 bg-red-50 hover:bg-red-100 text-red-600 text-sm font-semibold rounded-lg border border-red-200 transition-colors">
                  Clear All
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <p className="text-sm font-medium text-slate-500">
            {loading ? 'Loading…' : <><span className="font-bold text-slate-800">{companies.length}</span> buyers found</>}
          </p>
        </div>

        {loading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="bg-white rounded-2xl border border-slate-200 p-5 animate-pulse">
                <div className="h-4 bg-slate-100 rounded w-3/4 mb-3" />
                <div className="h-3 bg-slate-100 rounded w-1/2 mb-2" />
                <div className="h-3 bg-slate-100 rounded w-2/3 mb-4" />
                <div className="h-9 bg-slate-100 rounded-xl w-full" />
              </div>
            ))}
          </div>
        )}

        {error && (
          <div className="text-center py-16">
            <p className="text-red-500 font-medium">{error}</p>
            <button onClick={fetchCompanies} className="mt-3 text-sm text-slate-500 hover:text-slate-700 underline">Try again</button>
          </div>
        )}

        {!loading && !error && companies.length === 0 && (
          <div className="text-center py-20">
            <p className="text-5xl mb-4">🔍</p>
            <h3 className="font-bold text-slate-700 text-lg">No buyers found</h3>
            <p className="text-slate-400 mt-1 text-sm">Try adjusting your search or filters.</p>
            <button onClick={reset} className="mt-4 px-5 py-2 bg-blue-500 text-white rounded-xl font-bold text-sm">Clear Filters</button>
          </div>
        )}

        {!loading && !error && paginated.length > 0 && (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {paginated.map(company => (
                <div key={company.id} className="bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all flex flex-col">
                  <div className="p-5 flex-1">
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                        {company.name?.charAt(0)?.toUpperCase()}
                      </div>
                      <div className="flex items-center gap-1.5 ml-auto">
                        <WatchlistButton
                          isWatched={isInWatchlist(company.id)}
                          onToggle={() => toggleWatchlist({ id: company.id, name: company.name })}
                          size="small"
                        />

                      </div>
                    </div>

                    <h3 className="font-bold text-slate-900 text-sm leading-tight mb-3 line-clamp-2">{company.name}</h3>

                    <div className="flex flex-wrap gap-1.5">
                      {company.country && (
                        <span className="inline-flex items-center gap-1 text-xs text-slate-500 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded-full">
                          <MapPin size={10} />{company.country}
                        </span>
                      )}
                      {company.sector_name && (
                        <span className="inline-flex items-center gap-1 text-xs text-slate-500 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded-full">
                          <Tag size={10} />{company.sector_name}
                        </span>
                      )}
                      {company.type_name && (
                        <span className="inline-flex items-center gap-1 text-xs text-slate-500 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded-full">
                          <Building2 size={10} />{company.type_name}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="px-5 pb-5">
                    <Link
                      to={`/trade-directory/company/${company.id}`}
                      className="block w-full text-center py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-bold rounded-xl transition-colors"
                    >
                      View Profile & Contacts
                    </Link>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-8">
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={setCurrentPage}
                totalItems={sorted.length}
                itemsPerPage={itemsPerPage}
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default FindBuyers;
