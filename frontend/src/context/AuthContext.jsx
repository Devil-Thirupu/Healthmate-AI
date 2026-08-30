import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('healthmate_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('healthmate_access_token'));
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const verifyUser = async () => {
      const storedToken = localStorage.getItem('healthmate_access_token');
      if (storedToken) {
        try {
          const res = await api.get('/auth/me');
          setUser(res.data);
          localStorage.setItem('healthmate_user', JSON.stringify(res.data));
        } catch (err) {
          console.error('Session expired or invalid:', err);
          logout();
        }
      }
      setIsLoading(false);
    };
    verifyUser();
  }, []);

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    const { access_token, refresh_token, user: userData } = res.data;
    localStorage.setItem('healthmate_access_token', access_token);
    localStorage.setItem('healthmate_refresh_token', refresh_token);
    localStorage.setItem('healthmate_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const register = async (payload) => {
    const res = await api.post('/auth/register', payload);
    const { access_token, refresh_token, user: userData } = res.data;
    localStorage.setItem('healthmate_access_token', access_token);
    localStorage.setItem('healthmate_refresh_token', refresh_token);
    localStorage.setItem('healthmate_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const logout = () => {
    localStorage.removeItem('healthmate_access_token');
    localStorage.removeItem('healthmate_refresh_token');
    localStorage.removeItem('healthmate_user');
    setToken(null);
    setUser(null);
  };

  const updateProfile = async (profileData) => {
    const res = await api.put('/auth/me', profileData);
    setUser(res.data);
    localStorage.setItem('healthmate_user', JSON.stringify(res.data));
    return res.data;
  };

  const changePassword = async (current_password, new_password) => {
    const res = await api.put('/auth/change-password', { current_password, new_password });
    return res.data;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        register,
        logout,
        updateProfile,
        changePassword,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
