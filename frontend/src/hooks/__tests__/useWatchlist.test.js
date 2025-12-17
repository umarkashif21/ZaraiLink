
import { renderHook, act } from '@testing-library/react';
import { useState } from 'react';


const useWatchlist = () => {
  const [watchlist, setWatchlist] = useState([]);

  const isWatched = (companyId) => watchlist.includes(companyId);

  const toggleWatchlist = (companyId) => {
    setWatchlist(prev => {
      if (prev.includes(companyId)) {
        return prev.filter(id => id !== companyId);
      }
      return [...prev, companyId];
    });
  };

  const clearWatchlist = () => {
    setWatchlist([]);
  };

  const addToWatchlist = (companyId) => {
    setWatchlist(prev => {
      if (!prev.includes(companyId)) {
        return [...prev, companyId];
      }
      return prev;
    });
  };

  return { watchlist, isWatched, toggleWatchlist, clearWatchlist, addToWatchlist };
};

describe('useWatchlist Hook', () => {
  test('initializes with empty watchlist', () => {
    const { result } = renderHook(() => useWatchlist());
    expect(result.current.watchlist).toEqual([]);
  });

  test('isWatched returns false for unwatched company', () => {
    const { result } = renderHook(() => useWatchlist());
    expect(result.current.isWatched(5)).toBe(false);
  });

  test('toggleWatchlist adds company to watchlist', () => {
    const { result } = renderHook(() => useWatchlist());
    
    act(() => {
      result.current.toggleWatchlist(5);
    });

    expect(result.current.watchlist).toContain(5);
    expect(result.current.isWatched(5)).toBe(true);
  });

  test('toggleWatchlist removes company from watchlist', () => {
    const { result } = renderHook(() => useWatchlist());
    
    act(() => {
      result.current.toggleWatchlist(5);
    });
    expect(result.current.isWatched(5)).toBe(true);

    act(() => {
      result.current.toggleWatchlist(5);
    });
    expect(result.current.isWatched(5)).toBe(false);
  });

  test('addToWatchlist adds new company', () => {
    const { result } = renderHook(() => useWatchlist());
    
    act(() => {
      result.current.addToWatchlist(10);
    });

    expect(result.current.watchlist).toContain(10);
  });

  test('addToWatchlist does not duplicate', () => {
    const { result } = renderHook(() => useWatchlist());
    
    act(() => {
      result.current.addToWatchlist(10);
      result.current.addToWatchlist(10);
    });

    expect(result.current.watchlist.filter(id => id === 10).length).toBe(1);
  });

  test('clearWatchlist removes all items', () => {
    const { result } = renderHook(() => useWatchlist());
    
    act(() => {
      result.current.toggleWatchlist(1);
      result.current.toggleWatchlist(2);
      result.current.toggleWatchlist(3);
    });
    expect(result.current.watchlist.length).toBe(3);

    act(() => {
      result.current.clearWatchlist();
    });
    expect(result.current.watchlist).toEqual([]);
  });
});
