import { useState, useEffect, useCallback } from 'react';

const ACTIVITY_KEY = 'zarailink-activity';
const MAX_HISTORY = 50;


const useActivityHistory = () => {
  const [activities, setActivities] = useState(() => {
    try {
      const saved = localStorage.getItem(ACTIVITY_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    localStorage.setItem(ACTIVITY_KEY, JSON.stringify(activities.slice(0, MAX_HISTORY)));
  }, [activities]);

  const addActivity = useCallback((type, data) => {
    const activity = {
      id: Date.now(),
      type,
      data,
      timestamp: new Date().toISOString(),
    };
    
    setActivities(prev => [activity, ...prev].slice(0, MAX_HISTORY));
  }, []);

  const logCompanyView = useCallback((company) => {
    addActivity('company_view', {
      companyId: company.id,
      companyName: company.name || company.company,
    });
  }, [addActivity]);

  const logSearch = useCallback((query, resultCount) => {
    addActivity('search', { query, resultCount });
  }, [addActivity]);

  const logContactUnlock = useCallback((contact, company) => {
    addActivity('contact_unlock', {
      contactName: contact.name,
      companyName: company.name,
    });
  }, [addActivity]);

  const logExport = useCallback((type, itemCount) => {
    addActivity('export', { type, itemCount });
  }, [addActivity]);

  const getRecentActivities = useCallback((count = 10) => {
    return activities.slice(0, count);
  }, [activities]);

  const getActivitiesByType = useCallback((type) => {
    return activities.filter(a => a.type === type);
  }, [activities]);

  const clearHistory = useCallback(() => {
    setActivities([]);
    localStorage.removeItem(ACTIVITY_KEY);
  }, []);

  return {
    activities,
    addActivity,
    logCompanyView,
    logSearch,
    logContactUnlock,
    logExport,
    getRecentActivities,
    getActivitiesByType,
    clearHistory,
  };
};

export default useActivityHistory;
