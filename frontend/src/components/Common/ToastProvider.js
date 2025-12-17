import React from 'react';
import { Toaster } from 'react-hot-toast';
import { useTheme } from '../../context/ThemeContext';

const ToastProvider = ({ children }) => {
  const { isDarkMode } = useTheme();

  return (
    <>
      {children}
      <Toaster
        position="top-right"
        reverseOrder={false}
        gutter={12}
        containerStyle={{
          top: 80, 
        }}
        toastOptions={{
          
          duration: 4000,
          style: {
            background: isDarkMode ? '#1e293b' : '#ffffff',
            color: isDarkMode ? '#f1f5f9' : '#1a1a1a',
            border: `1px solid ${isDarkMode ? '#334155' : '#e5e7eb'}`,
            borderRadius: '12px',
            padding: '16px 20px',
            boxShadow: isDarkMode 
              ? '0 10px 25px rgba(0, 0, 0, 0.4)' 
              : '0 10px 25px rgba(0, 0, 0, 0.1)',
            fontSize: '0.95rem',
            fontWeight: 500,
            maxWidth: '400px',
          },
          
          success: {
            iconTheme: {
              primary: '#10b981',
              secondary: '#ffffff',
            },
            style: {
              borderLeft: '4px solid #10b981',
            },
          },
          error: {
            iconTheme: {
              primary: '#ef4444',
              secondary: '#ffffff',
            },
            style: {
              borderLeft: '4px solid #ef4444',
            },
          },
          loading: {
            iconTheme: {
              primary: '#3b82f6',
              secondary: isDarkMode ? '#1e293b' : '#ffffff',
            },
          },
        }}
      />
    </>
  );
};

export default ToastProvider;
