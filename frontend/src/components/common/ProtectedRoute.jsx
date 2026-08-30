import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Activity } from 'lucide-react';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="flex items-center space-x-3 text-brand-600 dark:text-brand-400 animate-pulse">
          <Activity className="w-8 h-8 animate-spin" />
          <span className="text-xl font-semibold tracking-wide font-heading">HEALTHMATE AI</span>
        </div>
        <p className="text-xs text-slate-500 mt-2">Securing clinical session...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

export default ProtectedRoute;
