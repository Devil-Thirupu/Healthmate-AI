import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';
import { supabase } from '../services/supabaseClient';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('healthmate_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('healthmate_access_token'));
  const [isLoading, setIsLoading] = useState(true);

  // -----------------------------------------------------------------------
  // On mount: verify the stored FastAPI token is still valid,
  // then subscribe to Supabase auth state changes (if Supabase is configured)
  // -----------------------------------------------------------------------
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

    // Supabase auth state listener — keeps Supabase session in sync
    // when token is refreshed by Supabase (e.g. Google OAuth, magic link)
    let unsubscribe = () => {};
    if (supabase) {
      const { data: { subscription } } = supabase.auth.onAuthStateChange(
        async (event, session) => {
          if (event === 'SIGNED_OUT') {
            // Mirror sign-out from Supabase to local state
            setToken(null);
            setUser(null);
            localStorage.removeItem('healthmate_access_token');
            localStorage.removeItem('healthmate_refresh_token');
            localStorage.removeItem('healthmate_user');
          }
          // SIGNED_IN / TOKEN_REFRESHED: Supabase manages its own session;
          // FastAPI JWTs are managed by the interceptor in api.js
        }
      );
      unsubscribe = () => subscription?.unsubscribe?.();
    }

    return () => unsubscribe();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // -----------------------------------------------------------------------
  // Auth actions (all go through FastAPI backend — unchanged)
  // -----------------------------------------------------------------------

  const login = async (identifier, password) => {
    const payload = identifier.includes('@')
      ? { email: identifier, password }
      : { identifier, password };
    const res = await api.post('/auth/login', payload);
    const { access_token, refresh_token, user: userData } = res.data;
    localStorage.setItem('healthmate_access_token', access_token);
    localStorage.setItem('healthmate_refresh_token', refresh_token);
    localStorage.setItem('healthmate_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const loginMobile = async (phone_number, password) => {
    const res = await api.post('/auth/login-mobile', { phone_number, password });
    const { access_token, refresh_token, user: userData } = res.data;
    localStorage.setItem('healthmate_access_token', access_token);
    localStorage.setItem('healthmate_refresh_token', refresh_token);
    localStorage.setItem('healthmate_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const loginGoogle = async (id_token) => {
    const res = await api.post('/auth/google', { id_token });
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

  const logout = async () => {
    // Sign out of Supabase session (best-effort)
    if (supabase) {
      try { await supabase.auth.signOut(); } catch (_) { /* non-fatal */ }
    }
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
        loginMobile,
        loginGoogle,
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
