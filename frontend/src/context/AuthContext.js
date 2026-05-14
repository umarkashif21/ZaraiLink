import React, { createContext, useState, useContext, useEffect } from 'react';

const AuthContext = createContext(null);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const res = await fetch(`${process.env.REACT_APP_API_BASE_URL}/accounts/api/check-auth/`, {
        method: 'GET',
        credentials: 'include',
      });

      if (res.ok) {
        const data = await res.json();
        console.log("auth check", data?.authenticated);
        if (data.authenticated) {
          setUser(data.user);
        }
      }
    } catch (err) {
      console.error('Auth check failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const res = await fetch(`${process.env.REACT_APP_API_BASE_URL}/accounts/api/login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();
      console.log("login resp", res.status);

      if (res.ok) {
        setUser(data.user);
        return { success: true, user: data.user };
      } else {
        return { success: false, error: data.error, email_not_verified: data.email_not_verified };
      }
    } catch (err) {
      console.error('Login error:', err);
      return { success: false, error: 'Network error. Please check your connection.' };
    }
  };

  const logout = async () => {
    try {
      await fetch(`${process.env.REACT_APP_API_BASE_URL}/accounts/api/logout/`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setUser(null);
    }
  };

  const value = {
    user,
    loading,
    tokenBalance: user?.token_balance || 0,
    login,
    logout,
    isAuthenticated: !!user,
    refreshUser: checkAuthStatus,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
