import React from 'react';
import { NavLink, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard,
  FolderOpen,
  Pill,
  MessageSquare,
  FlaskConical,
  Apple,
  TrendingUp,
  Calendar,
  Settings,
  LogOut,
  Heart
} from 'lucide-react';

const navigationItems = [
  { name: 'Dashboard',       path: '/dashboard',        icon: LayoutDashboard },
  { name: 'Medical Records', path: '/records',          icon: FolderOpen },
  { name: 'Prescriptions',   path: '/prescriptions',    icon: Pill },
  { name: 'Lab Tests',       path: '/reports',          icon: FlaskConical },
  { name: 'AI Assistant',    path: '/ai-assistant',     icon: MessageSquare },
  { name: 'Nutrition',       path: '/nutrition',        icon: Apple },
  { name: 'Health Trends',   path: '/audit',            icon: TrendingUp },
  { name: 'Appointments',    path: '/appointments',     icon: Calendar },
  { name: 'My Doctors',      path: '/doctors',          icon: Heart },
  { name: 'Secure Sharing',  path: '/sharing',          icon: FolderOpen },
  { name: 'Settings',        path: '/settings',         icon: Settings },
];

const Sidebar = ({ isOpen, onClose }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const firstName = user?.full_name ? user.full_name.split(' ')[0] : 'User';
  const userInitial = firstName.charAt(0).toUpperCase();

  const handleLogout = () => {
    logout?.();
    navigate('/login');
  };

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 w-56 flex flex-col transition-transform duration-300 lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        style={{ background: 'linear-gradient(180deg, #0f2544 0%, #152b4e 100%)' }}
      >
        {/* Logo */}
        <div className="flex items-center space-x-2.5 px-5 py-5 border-b border-white/10">
          <div className="w-9 h-9 rounded-xl bg-teal-500 flex items-center justify-center shadow-lg shrink-0">
            <Heart className="w-5 h-5 text-white" strokeWidth={2.5} />
          </div>
          <div>
            <div className="text-white font-extrabold text-sm leading-tight">HealthMate AI</div>
            <div className="text-blue-300 text-[10px] font-medium">Your Health, Our Priority</div>
          </div>
        </div>

        {/* Nav Items */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => onClose?.()}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-teal-500/20 text-white border border-teal-500/30 shadow-sm'
                      : 'text-blue-200/80 hover:text-white hover:bg-white/8'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon className={`w-4.5 h-4.5 shrink-0 ${isActive ? 'text-teal-400' : 'text-blue-300/70'}`} />
                    <span>{item.name}</span>
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* User profile + logout */}
        <div className="px-3 pb-4 pt-2 border-t border-white/10 space-y-2">
          <Link
            to="/settings"
            onClick={() => onClose?.()}
            className="flex items-center space-x-3 px-3 py-2.5 rounded-xl hover:bg-white/8 transition-colors"
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-teal-400 to-blue-500 text-white font-bold text-xs flex items-center justify-center shrink-0 shadow">
              {userInitial}
            </div>
            <div className="min-w-0">
              <p className="text-white text-xs font-semibold truncate">{firstName}</p>
              <p className="text-blue-300/60 text-[10px] truncate">{user?.email || ''}</p>
            </div>
          </Link>
          <button
            onClick={handleLogout}
            className="w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-medium text-blue-200/70 hover:text-white hover:bg-white/8 transition-all"
          >
            <LogOut className="w-4 h-4 shrink-0 text-blue-300/60" />
            <span>Logout</span>
          </button>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
