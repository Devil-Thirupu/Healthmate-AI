import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard,
  FolderOpen,
  FileText,
  MessageSquare,
  Pill,
  Activity,
  Apple,
  Bookmark,
  Info,
  Stethoscope,
  Bell,
  Share2,
  ShieldCheck,
  Settings,
  PhoneCall,
  Sparkles,
  Calendar,
  Users,
  Lock
} from 'lucide-react';

const navigationItems = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Medical Records', path: '/records', icon: FolderOpen },
  { name: 'Report Viewer', path: '/reports', icon: FileText },
  { name: 'Health AI Assistant', path: '/ai-assistant', icon: MessageSquare },
  { name: 'Prescriptions', path: '/prescriptions', icon: Pill },
  { name: 'Nutrition & Targets', path: '/nutrition', icon: Apple },
  { name: 'Appointment Prep', path: '/appointment-prep', icon: Bookmark },
  { name: 'Secure Sharing', path: '/sharing', icon: Share2 },
  { name: 'Audit & Privacy', path: '/audit', icon: ShieldCheck },
  { name: 'Settings', path: '/settings', icon: Settings },
];

// Doctor Connect section — additive
const doctorConnectItems = [
  { name: 'My Doctors', path: '/doctors', icon: Stethoscope },
  { name: 'Appointments', path: '/appointments', icon: Calendar },
  { name: 'Doctor Sharing', path: '/doctor-sharing', icon: Lock },
];


const Sidebar = ({ isOpen, onClose }) => {
  const { user } = useAuth();

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-sm lg:hidden"
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col justify-between transition-transform duration-300 lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="p-5 border-b border-slate-100 dark:border-slate-800/80 flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-teal-600 flex items-center justify-center text-white shadow-sm shrink-0">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            </svg>
          </div>
          <div>
            <div className="flex items-center space-x-1">
              <span className="font-heading font-extrabold text-slate-900 dark:text-white text-base tracking-tight">
                HealthMate
              </span>
              <span className="font-heading font-extrabold text-teal-600 dark:text-teal-400 text-base">
                AI
              </span>
            </div>
            <p className="text-[9px] font-bold text-slate-400 uppercase tracking-widest leading-tight">
              CLINICAL PLATFORM
            </p>
          </div>
        </div>

        {/* Navigation Stream */}
        <div className="flex-1 p-3.5 space-y-1 overflow-y-auto">
          <nav className="space-y-1">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => onClose?.()}
                  className={({ isActive }) =>
                    `flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs transition-all ${
                      isActive
                        ? 'bg-[#ccfbf1] dark:bg-teal-950/70 text-[#0f766e] dark:text-teal-300 font-bold shadow-xs'
                        : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800/60 font-medium'
                    }`
                  }
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
          </nav>

          {/* ── Doctor Connect section ── */}
          <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
            <p className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-2 px-2">
              Doctor Connect
            </p>
            <nav className="space-y-1">
              {doctorConnectItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={() => onClose?.()}
                    className={({ isActive }) =>
                      `flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-xs transition-all ${
                        isActive
                          ? 'bg-[#ccfbf1] dark:bg-teal-950/70 text-[#0f766e] dark:text-teal-300 font-bold shadow-xs'
                          : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800/60 font-medium'
                      }`
                    }
                  >
                    <Icon className="w-4 h-4 shrink-0" />
                    <span>{item.name}</span>
                  </NavLink>
                );
              })}
            </nav>
          </div>
        </div>


        {/* Bottom Section: Clinical Help Card & User Profile */}
        <div className="p-3.5 border-t border-slate-100 dark:border-slate-800 space-y-3 shrink-0">
          {/* Need Clinical Help Card */}
          <div className="p-3.5 rounded-2xl bg-[#f8fafc] dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-700/60 space-y-1.5">
            <h4 className="text-xs font-bold text-slate-900 dark:text-white">
              Need Clinical Help?
            </h4>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-snug">
              Contact your care team or call primary triage desk.
            </p>
            <a
              href="tel:+18005550199"
              className="inline-flex items-center space-x-1.5 text-xs font-bold text-teal-700 dark:text-teal-400 hover:underline pt-0.5"
            >
              <span>Call Care Desk</span>
              <PhoneCall className="w-3 h-3" />
            </a>
          </div>

          {/* User Profile Bar */}
          <Link
            to="/settings"
            onClick={() => onClose?.()}
            className="flex items-center space-x-3 p-1.5 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors"
          >
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-teal-600 to-emerald-500 text-white font-bold text-xs flex items-center justify-center shadow-xs shrink-0">
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-bold text-slate-900 dark:text-white truncate">
                {user?.full_name || 'Clinical User'}
              </p>
              <p className="text-[10px] text-slate-400 truncate">
                {user?.role ? `${user.role.toUpperCase()} • ID #${user.id || '84920'}` : 'Clinician ID #84920'}
              </p>
            </div>
          </Link>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
