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
  // On mount: check Supabase session / verify FastAPI token
  // -----------------------------------------------------------------------
  useEffect(() => {
    const initAuth = async () => {
      // 1. Check Supabase session first (handles Google OAuth redirect)
      if (supabase) {
        try {
          const { data: { session } } = await supabase.auth.getSession();
          if (session?.user) {
            const sbUser = session.user;
            const profile = {
              id: sbUser.id,
              email: sbUser.email,
              full_name: sbUser.user_metadata?.full_name || sbUser.user_metadata?.name || sbUser.email.split('@')[0],
              role: sbUser.user_metadata?.role || 'patient',
              phone_number: sbUser.user_metadata?.phone_number || '',
              date_of_birth: sbUser.user_metadata?.date_of_birth || '',
              gender: sbUser.user_metadata?.gender || '',
              blood_group: sbUser.user_metadata?.blood_group || '',
              language_preference: sbUser.user_metadata?.language_preference || 'en',
            };
            setUser(profile);
            setToken(session.access_token);
            localStorage.setItem('healthmate_user', JSON.stringify(profile));
            localStorage.setItem('healthmate_access_token', session.access_token);
          }
        } catch (sbErr) {
          console.warn('[HealthMate] Supabase session check error:', sbErr);
        }
      }

      // 2. If we have a stored token and user, verify against FastAPI backend if available
      const storedToken = localStorage.getItem('healthmate_access_token');
      if (storedToken) {
        try {
          const res = await api.get('/auth/me');
          if (res.data) {
            setUser(res.data);
            localStorage.setItem('healthmate_user', JSON.stringify(res.data));
          }
        } catch (err) {
          // If 401 Unauthorized from backend, clear session
          if (err.response?.status === 401) {
            console.warn('[HealthMate] Backend session expired');
            logout();
          }
        }
      }
      setIsLoading(false);
    };

    initAuth();

    // -----------------------------------------------------------------------
    // Supabase auth state listener (Google OAuth callback, token refresh, sign-out)
    // -----------------------------------------------------------------------
    let unsubscribe = () => {};
    if (supabase) {
      const { data: { subscription } } = supabase.auth.onAuthStateChange(
        async (event, session) => {
          if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED' || event === 'USER_UPDATED') {
            if (session?.user) {
              const sbUser = session.user;
              const profile = {
                id: sbUser.id,
                email: sbUser.email,
                full_name: sbUser.user_metadata?.full_name || sbUser.user_metadata?.name || sbUser.email.split('@')[0],
                role: sbUser.user_metadata?.role || 'patient',
                phone_number: sbUser.user_metadata?.phone_number || '',
                date_of_birth: sbUser.user_metadata?.date_of_birth || '',
                gender: sbUser.user_metadata?.gender || '',
                blood_group: sbUser.user_metadata?.blood_group || '',
                language_preference: sbUser.user_metadata?.language_preference || 'en',
              };
              setUser(profile);
              setToken(session.access_token);
              localStorage.setItem('healthmate_user', JSON.stringify(profile));
              localStorage.setItem('healthmate_access_token', session.access_token);
              if (session.refresh_token) {
                localStorage.setItem('healthmate_refresh_token', session.refresh_token);
              }
            }
          } else if (event === 'SIGNED_OUT') {
            setToken(null);
            setUser(null);
            localStorage.removeItem('healthmate_access_token');
            localStorage.removeItem('healthmate_refresh_token');
            localStorage.removeItem('healthmate_user');
            localStorage.removeItem('healthmate_supabase_session');
          }
        }
      );
      unsubscribe = () => subscription?.unsubscribe?.();
    }

    return () => unsubscribe();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // -----------------------------------------------------------------------
  // Auth actions
  // -----------------------------------------------------------------------

  const login = async (identifier, password) => {
    // 1. Try FastAPI backend first
    try {
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

      // Best effort: also sign in to Supabase if email is used
      if (supabase && identifier.includes('@')) {
        try {
          await supabase.auth.signInWithPassword({ email: identifier, password });
        } catch (_) { /* non-blocking */ }
      }
      return userData;
    } catch (apiErr) {
      // 2. If backend is not available (or static hosting) and Supabase is configured:
      if (supabase && identifier.includes('@') && (!apiErr.response || apiErr.response.status >= 500 || apiErr.code === 'ERR_NETWORK')) {
        const { data, error } = await supabase.auth.signInWithPassword({
          email: identifier,
          password,
        });
        if (error) throw new Error(error.message);
        const sbUser = data.user;
        const profile = {
          id: sbUser.id,
          email: sbUser.email,
          full_name: sbUser.user_metadata?.full_name || sbUser.email.split('@')[0],
          role: sbUser.user_metadata?.role || 'patient',
          phone_number: sbUser.user_metadata?.phone_number || '',
        };
        setUser(profile);
        setToken(data.session.access_token);
        localStorage.setItem('healthmate_user', JSON.stringify(profile));
        localStorage.setItem('healthmate_access_token', data.session.access_token);
        return profile;
      }
      throw apiErr;
    }
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

  const loginGoogle = async () => {
    if (!supabase) {
      throw new Error('Google Sign-In requires Supabase credentials to be configured in frontend/.env');
    }
    const currentBase = window.location.origin + (import.meta.env.BASE_URL || '/');
    const redirectTo = currentBase.endsWith('/') ? `${currentBase}dashboard` : `${currentBase}/dashboard`;
    
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo,
        queryParams: {
          access_type: 'offline',
          prompt: 'consent',
        },
      },
    });
    if (error) {
      throw new Error(error.message || 'Google OAuth failed');
    }
    return data;
  };

  const register = async (payload) => {
    // Sanitize optional empty strings to null for backend schema
    const sanitized = { ...payload };
    for (const key of ['phone_number', 'date_of_birth', 'emergency_contact', 'allergies', 'chronic_conditions']) {
      if (sanitized[key] === '') {
        sanitized[key] = null;
      }
    }

    // 1. If Supabase is available, create the user in Supabase Auth
    if (supabase && sanitized.email && sanitized.password) {
      try {
        const { data: sbData, error: sbError } = await supabase.auth.signUp({
          email: sanitized.email,
          password: sanitized.password,
          options: {
            data: {
              full_name: sanitized.full_name,
              role: sanitized.role || 'patient',
              phone_number: sanitized.phone_number || '',
              date_of_birth: sanitized.date_of_birth || '',
              gender: sanitized.gender || 'Male',
              blood_group: sanitized.blood_group || 'O+',
              language_preference: sanitized.language_preference || 'en',
            },
          },
        });
        if (sbError) {
          // If error is duplicate, let it proceed to backend
          if (!sbError.message?.toLowerCase().includes('already')) {
            console.warn('[HealthMate] Supabase signUp note:', sbError.message);
          }
        }
      } catch (sbErr) {
        console.warn('[HealthMate] Supabase registration exception:', sbErr);
      }
    }

    // 2. Call FastAPI backend register endpoint
    try {
      const res = await api.post('/auth/register', sanitized);
      const { access_token, refresh_token, user: userData } = res.data;
      localStorage.setItem('healthmate_access_token', access_token);
      localStorage.setItem('healthmate_refresh_token', refresh_token);
      localStorage.setItem('healthmate_user', JSON.stringify(userData));
      setToken(access_token);
      setUser(userData);
      return userData;
    } catch (apiErr) {
      // 3. If backend is unreachable but Supabase registered the user:
      if (supabase && (!apiErr.response || apiErr.response.status >= 500 || apiErr.code === 'ERR_NETWORK')) {
        const profile = {
          email: sanitized.email,
          full_name: sanitized.full_name,
          role: sanitized.role || 'patient',
          phone_number: sanitized.phone_number || '',
          gender: sanitized.gender || 'Male',
          blood_group: sanitized.blood_group || 'O+',
        };
        setUser(profile);
        localStorage.setItem('healthmate_user', JSON.stringify(profile));
        return profile;
      }
      throw apiErr;
    }
  };

  const logout = async () => {
    if (supabase) {
      try { await supabase.auth.signOut(); } catch (_) { /* non-fatal */ }
    }
    localStorage.removeItem('healthmate_access_token');
    localStorage.removeItem('healthmate_refresh_token');
    localStorage.removeItem('healthmate_user');
    localStorage.removeItem('healthmate_supabase_session');
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
        isAuthenticated: !!token || !!user,
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

