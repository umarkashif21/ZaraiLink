import React, { useState } from 'react';
import useCompanyNotes from '../../hooks/useCompanyNotes';
import './CompanyNotes.css';

const CompanyNotes = ({ companyId, companyName }) => {
  const { getNote, setNote, deleteNote } = useCompanyNotes();
  const existingNote = getNote(companyId);
  const [isEditing, setIsEditing] = useState(false);
  const [content, setContent] = useState(existingNote?.content || '');

  const handleSave = () => {
    if (content.trim()) {
      setNote(companyId, content.trim());
    } else {
      deleteNote(companyId);
    }
    setIsEditing(false);
  };

  const handleCancel = () => {
    setContent(existingNote?.content || '');
    setIsEditing(false);
  };

  return (
    <div className="company-notes">
      <div className="notes-header">
        <h4>📝 Private Notes</h4>
        {!isEditing && existingNote && (
          <button className="edit-note-btn" onClick={() => setIsEditing(true)}>
            Edit
          </button>
        )}
      </div>

      {isEditing || !existingNote ? (
        <div className="notes-editor">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder={`Add private notes about ${companyName}...`}
            rows={4}
          />
          <div className="notes-actions">
            <button className="save-btn" onClick={handleSave}>
              💾 Save
            </button>
            {existingNote && (
              <button className="cancel-btn" onClick={handleCancel}>
                Cancel
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="notes-content">
          <p>{existingNote.content}</p>
          <span className="notes-date">
            Last updated: {new Date(existingNote.updatedAt).toLocaleDateString()}
          </span>
        </div>
      )}
    </div>
  );
};

export default CompanyNotes;
