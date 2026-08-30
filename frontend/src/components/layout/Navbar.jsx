import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  Activity,
  ShieldCheck,
  PlusCircle,
  Sun,
  Moon,
  LogOut,
  User,
  Settings,
  Menu,
  X,
  Languages,
  FileText
} from 'lucide-react';

const Navbar = ({ onOpenUpload, onToggleSidebar, isSidebarOpen }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(() => {
    return document.documentElement.classList.contains('dark');
  });

  const toggleDarkMode = () => {
    if (document.documentElement.classList.contains('dark')) {
      document.documentElement.classList.remove('dark');
      setIsDarkMode(false);
      localStorage.setItem('healthmate_theme', 'light');
    } else {
      document.documentElement.classList.add('dark');
      setIsDarkMode(true);
      localStorage.setItem('healthmate_theme', 'dark');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="sticky top-0 z-30 bg-white/95 dark:bg-slate-900/95 backdrop-blur border-b border-slate-200 dark:border-slate-800 transition-colors">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left: Mobile Menu + Logo */}
          <div className="flex items-center space-x-3">
            <button
              onClick={onToggleSidebar}
              className="lg:hidden p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 focus:outline-none"
              aria-label="Toggle sidebar"
            >
              {isSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>

            <Link to="/dashboard" className="flex items-center space-x-2.5 group">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-cyan-400 flex items-center justify-center text-white shadow-md shadow-brand-500/20 group-hover:scale-105 transition-transform">
                <Activity className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center space-x-1.5">
                  <span className="font-heading font-bold text-lg text-slate-900 dark:text-white tracking-tight">
                    HEALTHMATE
                  </span>
                  <span className="bg-brand-100 dark:bg-brand-950 text-brand-700 dark:text-brand-300 text-[10px] font-bold px-1.5 py-0.5 rounded tracking-wide">
                    AI
                  </span>
                </div>
                <p className="text-[10px] text-slate-400 dark:text-slate-400 hidden sm:block">
                  Personal Health Record & Medical Assistant
                </p>
              </div>
            </Link>
          </div>

          {/* Center: Privacy & Trilingual Indicators */}
          <div className="hidden md:flex items-center space-x-3">
            <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 text-emerald-700 dark:text-emerald-300 text-xs font-medium">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>SHA-256 Vault Isolated</span>
            </div>
            <div className="flex items-center space-x-1 px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-xs">
              <Languages className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400" />
              <span>EN • தமிழ் • Tanglish</span>
            </div>
          </div>

          {/* Right: Actions, Theme, User Dropdown */}
          <div className="flex items-center space-x-2.5">
            <button
              onClick={onOpenUpload}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-gradient-to-r from-brand-600 to-cyan-600 hover:from-brand-700 hover:to-cyan-700 text-white text-xs font-semibold rounded-lg shadow-sm shadow-brand-600/30 transition-all active:scale-95"
            >
              <PlusCircle className="w-4 h-4" />
              <span className="hidden sm:inline">Upload Record</span>
            </button>

            {/* Dark Mode Toggle */}
            <button
              onClick={toggleDarkMode}
              className="p-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-white dark:hover:bg-slate-800 transition-colors"
              title="Toggle theme"
            >
              {isDarkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
            </button>

            {/* User Profile Menu */}
            <div className="relative">
              <button
                onClick={() => setIsProfileOpen(!isProfileOpen)}
                className="flex items-center space-x-2 p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-500 to-teal-500 text-white font-semibold text-xs flex items-center justify-center">
                  {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
                </div>
                <div className="hidden xl:block text-left text-xs">
                  <p className="font-semibold text-slate-800 dark:text-slate-200 truncate max-w-[120px]">
                    {user?.full_name || 'Patient'}
                  </p>
                  <p className="text-[10px] text-slate-400 capitalize">{user?.role || 'patient'}</p>
                </div>
              </button>

              {isProfileOpen && (
                <div
                  className="absolute right-0 mt-2 w-56 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-slate-100 dark:border-slate-700 py-1.5 z-50 animate-in fade-in zoom-in-95 duration-100"
                  onClick={() => setIsProfileOpen(false)}
                >
                  <div className="px-3.5 py-2 border-b border-slate-100 dark:border-slate-700">
                    <p className="text-xs font-semibold text-slate-900 dark:text-white truncate">
                      {user?.full_name}
                    </p>
                    <p className="text-[11px] text-slate-400 truncate">{user?.email}</p>
                    {user?.blood_group && (
                      <span className="inline-block mt-1 text-[10px] font-bold px-1.5 py-0.5 bg-rose-50 dark:bg-rose-950/60 text-rose-600 dark:text-rose-400 rounded">
                        Blood Group: {user.blood_group}
                      </span>
                    )}
                  </div>

                  <Link
                    to="/settings"
                    className="flex items-center space-x-2 px-3.5 py-2 text-xs text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700/50"
                  >
                    <User className="w-4 h-4 text-slate-400" />
                    <span>My Health Profile</span>
                  </Link>

                  <Link
                    to="/settings"
                    className="flex items-center space-x-2 px-3.5 py-2 text-xs text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700/50"
                  >
                    <Settings className="w-4 h-4 text-slate-400" />
                    <span>Account Settings</span>
                  </Link>

                  <div className="border-t border-slate-100 dark:border-slate-700 my-1"></div>

                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center space-x-2 px-3.5 py-2 text-xs text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 text-left"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Sign Out</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
