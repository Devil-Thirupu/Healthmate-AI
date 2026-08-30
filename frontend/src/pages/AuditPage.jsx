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
  Loader2
} from 'lucide-react';

const AuditPage = () => {
  const [logs, setLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('all');

  const fetchAuditLogs = async () => {
    try {
      setIsLoading(true);
      const params = {};
      if (actionFilter !== 'all') params.action = actionFilter;
      const res = await api.get('/audit/', { params });
      setLogs(res.data || []);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
  }, [actionFilter]);

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white font-heading">
            Audit & Compliance Log
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Tamper-evident chronological log of all document views, uploads, downloads, sharing, and authentications
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="px-3 py-1.5 text-xs rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            <option value="all">All Actions</option>
            <option value="AUTH_LOGIN_SUCCESS">Logins</option>
            <option value="DOC_UPLOAD">Document Uploads</option>
            <option value="DOC_VIEW">Document Views</option>
            <option value="DOC_DOWNLOAD">Document Downloads</option>
            <option value="SHARE_CREATE">Share Links Created</option>
            <option value="SHARE_ACCESS_SUCCESS">Share Links Accessed</option>
            <option value="USER_PROFILE_UPDATE">Profile Updates</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="p-16 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
          <Loader2 className="w-7 h-7 animate-spin text-brand-600 mx-auto mb-2" />
          <p className="text-xs text-slate-500">Loading audit records...</p>
        </div>
      ) : logs.length === 0 ? (
        <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 space-y-2">
          <ShieldAlert className="w-10 h-10 text-slate-300 dark:text-slate-600 mx-auto" />
          <p className="text-xs text-slate-500">No audit events recorded for this filter</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden divide-y divide-slate-100 dark:divide-slate-800">
          {logs.map((log) => (
            <div key={log.id} className="p-4 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors flex items-start justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-brand-50 dark:bg-brand-950/60 text-brand-700 dark:text-brand-300 border border-brand-200 dark:border-brand-800">
                    {log.action.replace(/_/g, ' ')}
                  </span>
                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 capitalize">
                    {log.resource_type} {log.resource_id ? `#${log.resource_id}` : ''}
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400">
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
                  <div className="pt-1 text-[11px] text-slate-500 dark:text-slate-400 font-mono bg-slate-50 dark:bg-slate-800/60 p-2 rounded-lg inline-block">
                    {JSON.stringify(log.details_json)}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AuditPage;
