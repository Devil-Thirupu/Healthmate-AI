import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderOpen,
  FlaskConical,
  Pill,
  BotMessageSquare,
  Share2,
  ShieldAlert,
  Settings,
  HeartHandshake,
  AlertTriangle
} from 'lucide-react';

const navigationItems = [
  { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { name: 'Medical Records', path: '/records', icon: FolderOpen },
  { name: 'Lab Reports', path: '/reports', icon: FlaskConical },
  { name: 'Prescriptions', path: '/prescriptions', icon: Pill },
  { name: 'AI Assistant', path: '/ai-assistant', icon: BotMessageSquare, highlight: true },
  { name: 'Patient Sharing', path: '/sharing', icon: Share2 },
  { name: 'Audit & Privacy', path: '/audit', icon: ShieldAlert },
  { name: 'Settings & Profile', path: '/settings', icon: Settings },
];

const Sidebar = ({ isOpen, onClose }) => {
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-sm lg:hidden"
        />
      )}

      <aside
        className={`fixed top-16 bottom-0 left-0 z-40 w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col justify-between transition-transform duration-300 lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-4 space-y-1.5 overflow-y-auto">
          <p className="px-3 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
            Clinical Hub
          </p>

          <nav className="space-y-1">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => onClose?.()}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all ${
                      isActive
                        ? 'bg-brand-500/10 text-brand-600 dark:text-brand-400 font-semibold border-l-4 border-brand-600'
                        : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800/60'
                    } ${item.highlight && !item.isActive ? 'text-cyan-600 dark:text-cyan-400' : ''}`
                  }
                >
                  <div className="flex items-center space-x-3">
                    <Icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </div>
                  {item.highlight && (
                    <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-cyan-100 dark:bg-cyan-950 text-cyan-700 dark:text-cyan-300">
                      RAG
                    </span>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Bottom Safety & Disclaimer Card */}
        <div className="p-4 border-t border-slate-100 dark:border-slate-800">
          <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60">
            <div className="flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-[11px] font-bold text-amber-800 dark:text-amber-300">
                  Clinical Safety Guard
                </p>
                <p className="text-[10px] text-amber-700 dark:text-amber-400/90 leading-tight mt-0.5">
                  AI answers are strictly evidence-grounded. Consult your licensed doctor for diagnoses and prescriptions.
                </p>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
