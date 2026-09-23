import React, { useState, useEffect } from 'react';
import api from '../services/api';
import {
  ShieldAlert,
  Search,
  Filter,
  CheckCircle2,
  Calendar,
  Globe,
  Clock,
  Eye,
  User,
  FileText,
  Sparkles,
  Share2,
  LogIn,
  Key,
  ShieldCheck,
  Loader2
} from 'lucide-react';

const CATEGORIES = [
  { id: 'all', label: 'All Activity' },
  { id: 'login', label: 'Login & Auth', icon: LogIn },
  { id: 'documents', label: 'Documents', icon: FileText },
  { id: 'ai', label: 'AI Intelligence', icon: Sparkles },
  { id: 'sharing', label: 'Sharing', icon: Share2 },
];

const AuditPage = () => {
  const [logs, setLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');

  const fetchAuditLogs = async (category = 'all') => {
    try {
      setIsLoading(true);
      const params = {};
      if (category !== 'all') params.category = category;
      const res = await api.get('/audit', { params });
      setLogs(res.data || []);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs(selectedCategory);
  }, [selectedCategory]);

  const getActionBadge = (action) => {
    if (action.includes('LOGIN_SUCCESS') || action.includes('REGISTER')) {
      return { bg: 'bg-emerald-50 text-emerald-700 border border-emerald-200', icon: LogIn };
    }
    if (action.includes('FAILED') || action.includes('REVOKE')) {
      return { bg: 'bg-rose-50 text-rose-700 border border-rose-200', icon: ShieldAlert };
    }
    if (action.includes('SHARE')) {
      return { bg: 'bg-teal-50 text-teal-700 border border-teal-200', icon: Share2 };
    }
    if (action.includes('AI') || action.includes('ASSISTANT')) {
      return { bg: 'bg-sky-50 text-sky-700 border border-sky-200', icon: Sparkles };
    }
    return { bg: 'bg-slate-100 text-slate-700 border border-slate-200', icon: FileText };
  };

  return (
    <div className="space-y-6 max-w-5xl pb-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
              Security & Activity Audit Dashboard
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-teal-50 text-teal-700 border border-teal-200">
              Zero-Exposure Privacy
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Tamper-evident activity trail for logins, document operations, AI summaries, and record sharing.
          </p>
        </div>

        <div className="flex items-center space-x-2 bg-white dark:bg-slate-900 px-3.5 py-2 rounded-xl border border-slate-200/90 dark:border-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-300 shadow-2xs">
          <ShieldCheck className="w-4 h-4 text-teal-600" />
          <span>Patient Vault Protected</span>
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setSelectedCategory(cat.id)}
            className={`px-3.5 py-1.5 rounded-xl font-bold transition-all shrink-0 cursor-pointer ${
              selectedCategory === cat.id
                ? 'bg-teal-600 text-white shadow-xs'
                : 'bg-white dark:bg-slate-800 border border-slate-200/90 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="p-16 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs">
          <Loader2 className="w-7 h-7 animate-spin text-teal-600 mx-auto mb-2" />
          <p className="text-xs text-slate-500">Loading audit records...</p>
        </div>
      ) : logs.length === 0 ? (
        <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 space-y-2">
          <ShieldAlert className="w-10 h-10 text-slate-300 dark:text-slate-600 mx-auto" />
          <p className="text-xs text-slate-500 font-medium">No activity logged for this category filter.</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs overflow-hidden divide-y divide-slate-100 dark:divide-slate-800">
          {logs.map((log) => {
            const badge = getActionBadge(log.action);
            const Icon = badge.icon;
            return (
              <div
                key={log.id}
                className="p-4 hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors flex items-start justify-between gap-4"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center space-x-2">
                    <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md flex items-center space-x-1 ${badge.bg}`}>
                      <Icon className="w-3 h-3 mr-1" />
                      <span>{log.action.replace(/_/g, ' ')}</span>
                    </span>
                    <span className="text-xs font-bold text-slate-800 dark:text-slate-200 capitalize">
                      {log.resource_type} {log.resource_id ? `(#${log.resource_id})` : ''}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 font-medium">
                    <span className="flex items-center space-x-1">
                      <Clock className="w-3 h-3 text-slate-400" />
                      <span>{new Date(log.created_at).toLocaleString()}</span>
                    </span>
                    {log.ip_address && (
                      <span className="flex items-center space-x-1">
                        <Globe className="w-3 h-3 text-slate-400" />
                        <span>IP: {log.ip_address}</span>
                      </span>
                    )}
                  </div>

                  {log.details_json && Object.keys(log.details_json).length > 0 && (
                    <div className="pt-0.5 text-[11px] text-slate-600 dark:text-slate-400 font-mono bg-slate-50 dark:bg-slate-800/50 p-2 rounded-lg border border-slate-100 dark:border-slate-800 inline-block">
                      {Object.entries(log.details_json).map(([k, v]) => (
                        <span key={k} className="mr-3 inline-block">
                          <strong className="font-semibold text-slate-500 capitalize">{k.replace('_', ' ')}:</strong> {String(v)}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default AuditPage;
