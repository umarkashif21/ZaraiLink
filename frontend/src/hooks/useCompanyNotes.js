import { useState, useEffect, useCallback } from 'react';

const NOTES_KEY = 'zarailink-notes';


const useCompanyNotes = () => {
  const [notes, setNotes] = useState(() => {
    try {
      const saved = localStorage.getItem(NOTES_KEY);
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });

  useEffect(() => {
    localStorage.setItem(NOTES_KEY, JSON.stringify(notes));
  }, [notes]);

  const getNote = useCallback((companyId) => {
    return notes[companyId] || null;
  }, [notes]);

  const setNote = useCallback((companyId, content) => {
    setNotes(prev => ({
      ...prev,
      [companyId]: {
        content,
        updatedAt: new Date().toISOString(),
        createdAt: prev[companyId]?.createdAt || new Date().toISOString(),
      }
    }));
  }, []);

  const deleteNote = useCallback((companyId) => {
    setNotes(prev => {
      const updated = { ...prev };
      delete updated[companyId];
      return updated;
    });
  }, []);

  const hasNote = useCallback((companyId) => {
    return !!notes[companyId];
  }, [notes]);

  const getAllNotes = useCallback(() => {
    return Object.entries(notes).map(([companyId, note]) => ({
      companyId,
      ...note,
    }));
  }, [notes]);

  return {
    getNote,
    setNote,
    deleteNote,
    hasNote,
    getAllNotes,
    notesCount: Object.keys(notes).length,
  };
};

export default useCompanyNotes;
