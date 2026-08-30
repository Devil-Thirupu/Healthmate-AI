import React, { useState, useEffect } from 'react';
import api from '../services/api';
import {
  Share2,
  Lock,
  PlusCircle,
  Clock,
  Trash2,
  Copy,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  Calendar,
  Eye,
  Loader2
} from 'lucide-react';

const SharingPage = () => {
  const [links, setLinks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [copiedToken, setCopiedToken] = useState(null);

  const [formData, setFormData] = useState({
    title: 'Physician Consultation Records',
    recipient_name: '',
    duration_hours: 48,
    is_pin_protected: true,
    pin: '1234',
    max_access_count: 5,
    allow_download: true,
    allow_ai_summary: true,
  });

  const fetchLinks = async () => {
    try {
      setIsLoading(true);
      const res = await api.get('/sharing/my-links');
      setLinks(res.data || []);
    } catch (err) {
      console.error('Failed to load shared links:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLinks();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setIsCreating(true);
    try {
      await api.post('/sharing/create', formData);
      setFormData({
        title: 'Physician Consultation Records',
        recipient_name: '',
        duration_hours: 48,
        is_pin_protected: true,
        pin: '1234',
        max_access_count: 5,
        allow_download: true,
        allow_ai_summary: true,
      });
      fetchLinks();
    } catch (err) {
      console.error('Failed to create share link:', err);
    } finally {
      setIsCreating(false);
    }
  };

  const handleRevoke = async (id) => {
    try {
      await api.delete(`/sharing/${id}`);
      fetchLinks();
    } catch (err) {
      console.error('Failed to revoke link:', err);
    }
  };

  const handleCopyLink = (token) => {
    const fullUrl = `${window.location.origin}/share/${token}`;
    navigator.clipboard.writeText(fullUrl);
    setCopiedToken(token);
    setTimeout(() => setCopiedToken(null), 2500);
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white font-heading">
          Patient-Controlled Temporary Sharing
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Generate secure, auto-expiring, PIN-protected medical access links for consulting physicians
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Create Link Card */}
        <div className="p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex items-center space-x-2.5 pb-2 border-b border-slate-100 dark:border-slate-800">
            <div className="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
              <Share2 className="w-4 h-4" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Create New Share Link
            </h3>
          </div>

          <form onSubmit={handleCreate} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Link Title / Purpose
              </label>
              <input
                type="text"
                required
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Doctor or Clinic Name
              </label>
              <input
                type="text"
                value={formData.recipient_name}
                onChange={(e) => setFormData({ ...formData, recipient_name: e.target.value })}
                placeholder="e.g. Dr. Ramachandran (Apollo)"
                className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Expiry Duration
                </label>
                <select
                  value={formData.duration_hours}
                  onChange={(e) => setFormData({ ...formData, duration_hours: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value={12}>12 Hours</option>
                  <option value={24}>24 Hours</option>
                  <option value={48}>48 Hours (2 Days)</option>
                  <option value={168}>7 Days</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Max Views
                </label>
                <input
                  type="number"
                  min={1}
                  max={50}
                  value={formData.max_access_count}
                  onChange={(e) => setFormData({ ...formData, max_access_count: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  PIN Protection
                </label>
                <input
                  type="checkbox"
                  checked={formData.is_pin_protected}
                  onChange={(e) => setFormData({ ...formData, is_pin_protected: e.target.checked })}
                  className="rounded text-brand-600 focus:ring-brand-500"
                />
              </div>
              {formData.is_pin_protected && (
                <input
                  type="text"
                  maxLength={6}
                  value={formData.pin}
                  onChange={(e) => setFormData({ ...formData, pin: e.target.value })}
                  placeholder="Enter 4-6 digit numeric PIN"
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              )}
            </div>

            <button
              type="submit"
              disabled={isCreating}
              className="w-full py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white text-xs font-semibold rounded-xl shadow-md transition-all flex items-center justify-center space-x-2"
            >
              {isCreating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Generating Secure Link...</span>
                </>
              ) : (
                <>
                  <Lock className="w-4 h-4" />
                  <span>Generate Share Link</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Existing Links List */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white font-heading">
            Active & Past Share Links
          </h3>

          {isLoading ? (
            <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
              <Loader2 className="w-6 h-6 animate-spin text-brand-600 mx-auto mb-2" />
              <p className="text-xs text-slate-500">Loading share links...</p>
            </div>
          ) : links.length === 0 ? (
            <div className="p-10 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 space-y-2">
              <Share2 className="w-10 h-10 text-slate-300 dark:text-slate-600 mx-auto" />
              <p className="text-xs text-slate-500">No active sharing links generated yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {links.map((link) => (
                <div
                  key={link.id}
                  className={`p-4 rounded-2xl bg-white dark:bg-slate-900 border transition-all space-y-3 ${
                    link.is_active
                      ? 'border-slate-200 dark:border-slate-800 shadow-sm'
                      : 'border-slate-100 dark:border-slate-800/60 opacity-60'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center space-x-2">
                        <h4 className="text-xs font-bold text-slate-900 dark:text-white">
                          {link.title}
                        </h4>
                        <span
                          className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded ${
                            link.is_active
                              ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300'
                              : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                          }`}
                        >
                          {link.is_active ? 'Active' : 'Revoked'}
                        </span>
                        {link.is_pin_protected && (
                          <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300 flex items-center space-x-1">
                            <Lock className="w-2.5 h-2.5" />
                            <span>PIN Protected</span>
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        Recipient: {link.recipient_name || 'General Doctor Access'} • Views: {link.access_count} / {link.max_access_count}
                      </p>
                    </div>

                    <div className="flex items-center space-x-1.5">
                      {link.is_active && (
                        <button
                          onClick={() => handleCopyLink(link.token)}
                          className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-brand-50 dark:bg-brand-950 text-brand-600 dark:text-brand-400 hover:bg-brand-100 transition-colors flex items-center space-x-1"
                        >
                          {copiedToken === link.token ? (
                            <>
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                              <span>Copied!</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5" />
                              <span>Copy Link</span>
                            </>
                          )}
                        </button>
                      )}

                      {link.is_active && (
                        <button
                          onClick={() => handleRevoke(link.id)}
                          className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors"
                          title="Revoke Access"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-4 text-[10px] text-slate-400 pt-1 border-t border-slate-100 dark:border-slate-800">
                    <span>Expires: {new Date(link.expires_at).toLocaleString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SharingPage;
