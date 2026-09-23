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
  FileText,
  FlaskConical,
  Pill,
  Activity,
  User,
  ExternalLink,
  Loader2,
  ShieldAlert
} from 'lucide-react';

const EXPIRY_OPTIONS = [
  { label: '1 Hour', hours: 1 },
  { label: '6 Hours', hours: 6 },
  { label: '24 Hours (1 Day)', hours: 24 },
  { label: '3 Days (72 Hours)', hours: 72 },
  { label: '7 Days (1 Week)', hours: 168 },
];

const SharingPage = () => {
  const [links, setLinks] = useState([]);
  const [userDocs, setUserDocs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [copiedToken, setCopiedToken] = useState(null);

  const [formData, setFormData] = useState({
    title: 'Consultation Records',
    recipient_name: '',
    duration_hours: 24,
    permission: 'READ_ONLY',
    is_pin_protected: false,
    pin: '',
    max_access_count: 20,
    selected_doc_ids: [],
    selected_lab_ids: [],
    selected_rx_ids: [],
    allow_download: false,
    allow_ai_summary: true,
  });

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const [linksRes, docsRes] = await Promise.allSettled([
        api.get('/sharing/my-links'),
        api.get('/documents/'),
      ]);

      if (linksRes.status === 'fulfilled') setLinks(linksRes.value.data || []);
      if (docsRes.status === 'fulfilled') {
        const docs = docsRes.value.data || [];
        setUserDocs(docs);
        if (docs.length > 0) {
          setFormData((prev) => ({
            ...prev,
            selected_doc_ids: [docs[0].id]
          }));
        }
      }
    } catch (err) {
      console.error('Failed to load sharing resources:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleToggleDoc = (docId) => {
    setFormData((prev) => {
      const exists = prev.selected_doc_ids.includes(docId);
      return {
        ...prev,
        selected_doc_ids: exists
          ? prev.selected_doc_ids.filter((id) => id !== docId)
          : [...prev.selected_doc_ids, docId]
      };
    });
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (formData.selected_doc_ids.length === 0) {
      alert('Please select at least one medical document or record to share.');
      return;
    }
    setIsCreating(true);
    try {
      await api.post('/sharing/create', {
        title: formData.title,
        recipient_name: formData.recipient_name,
        document_ids: formData.selected_doc_ids,
        duration_hours: formData.duration_hours,
        permission: 'READ_ONLY',
        is_pin_protected: formData.is_pin_protected,
        pin: formData.pin,
        max_access_count: formData.max_access_count,
        allow_download: formData.allow_download,
        allow_ai_summary: formData.allow_ai_summary
      });
      setFormData({
        title: 'Consultation Records',
        recipient_name: '',
        duration_hours: 24,
        permission: 'READ_ONLY',
        is_pin_protected: false,
        pin: '',
        max_access_count: 20,
        selected_doc_ids: userDocs.length > 0 ? [userDocs[0].id] : [],
        selected_lab_ids: [],
        selected_rx_ids: [],
        allow_download: false,
        allow_ai_summary: true,
      });
      fetchData();
    } catch (err) {
      console.error('Failed to create share link:', err);
      alert(err.response?.data?.detail || 'Failed to create share link.');
    } finally {
      setIsCreating(false);
    }
  };

  const handleRevoke = async (id) => {
    try {
      await api.post(`/sharing/${id}/revoke`);
      fetchData();
    } catch (err) {
      console.error('Failed to revoke link:', err);
    }
  };

  const handleCopyLink = (token) => {
    const fullUrl = `${window.location.origin}/shared/${token}`;
    navigator.clipboard.writeText(fullUrl);
    setCopiedToken(token);
    setTimeout(() => setCopiedToken(null), 2500);
  };

  return (
    <div className="space-y-6 max-w-6xl pb-10">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
              Patient-Controlled Record Sharing
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-teal-50 text-teal-700 border border-teal-200">
              Zero-Exposure Privacy
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Generate temporary, auto-expiring, read-only medical access links with granular record selection and optional PIN lock.
          </p>
        </div>

        <div className="flex items-center space-x-2 bg-white dark:bg-slate-900 px-3.5 py-2 rounded-xl border border-slate-200/90 dark:border-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-300 shadow-2xs">
          <ShieldCheck className="w-4 h-4 text-teal-600" />
          <span>Patient Vault Protected</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Create Link Card */}
        <div className="lg:col-span-1 p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-4">
          <div className="flex items-center space-x-2.5 pb-3 border-b border-slate-100 dark:border-slate-800">
            <div className="w-8 h-8 rounded-lg bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-400 flex items-center justify-center">
              <Share2 className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Create Temporary Share
              </h3>
              <span className="text-[10px] font-bold text-teal-600 uppercase">
                Default: READ ONLY
              </span>
            </div>
          </div>

          <form onSubmit={handleCreate} className="space-y-3.5">
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                Recipient / Physician Name
              </label>
              <input
                type="text"
                value={formData.recipient_name}
                onChange={(e) => setFormData({ ...formData, recipient_name: e.target.value })}
                placeholder="e.g. Dr. Ramachandran (Apollo)"
                className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-600 font-medium"
              />
            </div>

            {/* Select Specific Records */}
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                Select Medical Documents to Share ({formData.selected_doc_ids.length} selected)
              </label>
              {userDocs.length === 0 ? (
                <p className="text-[11px] text-slate-400 italic py-2">
                  No documents in vault yet. Upload documents first.
                </p>
              ) : (
                <div className="max-h-44 overflow-y-auto space-y-1.5 p-2 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  {userDocs.map((doc) => {
                    const isSelected = formData.selected_doc_ids.includes(doc.id);
                    return (
                      <div
                        key={doc.id}
                        onClick={() => handleToggleDoc(doc.id)}
                        className={`p-2 rounded-lg text-xs cursor-pointer flex items-center justify-between transition-colors ${
                          isSelected
                            ? 'bg-teal-50 dark:bg-teal-950/80 border border-teal-200 dark:border-teal-800 text-teal-900 dark:text-teal-200 font-bold'
                            : 'bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 font-medium'
                        }`}
                      >
                        <div className="truncate max-w-[200px]">
                          <p className="truncate text-[11px]">{doc.title || doc.original_filename}</p>
                          <span className="text-[9px] text-slate-400 uppercase font-bold">{doc.category}</span>
                        </div>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => {}}
                          className="rounded text-teal-600 pointer-events-none"
                        />
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Expiry Selection */}
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                Expiration Duration
              </label>
              <select
                value={formData.duration_hours}
                onChange={(e) => setFormData({ ...formData, duration_hours: parseInt(e.target.value) })}
                className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-600 font-medium"
              >
                {EXPIRY_OPTIONS.map((opt) => (
                  <option key={opt.hours} value={opt.hours}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Optional PIN */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-bold text-slate-700 dark:text-slate-300">
                  PIN Protection (Optional)
                </label>
                <input
                  type="checkbox"
                  checked={formData.is_pin_protected}
                  onChange={(e) => setFormData({ ...formData, is_pin_protected: e.target.checked })}
                  className="rounded text-teal-600 focus:ring-teal-600"
                />
              </div>
              {formData.is_pin_protected && (
                <input
                  type="text"
                  maxLength={6}
                  value={formData.pin}
                  onChange={(e) => setFormData({ ...formData, pin: e.target.value })}
                  placeholder="Enter 4-6 digit PIN (e.g. 1234)"
                  className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-600 font-mono tracking-wider mt-1"
                />
              )}
            </div>

            <button
              type="submit"
              disabled={isCreating || userDocs.length === 0}
              className="w-full py-2.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl shadow-xs transition-all flex items-center justify-center space-x-2 disabled:opacity-50 cursor-pointer"
            >
              {isCreating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Generating Secure Link...</span>
                </>
              ) : (
                <>
                  <Lock className="w-4 h-4" />
                  <span>Generate Read-Only Access</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Existing Links Table & Management */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Active & Past Shares ({links.length})
            </h3>
            <span className="text-[11px] text-slate-500 font-medium">
              Immediate revocation instantly denies access
            </span>
          </div>

          {isLoading ? (
            <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs">
              <Loader2 className="w-6 h-6 animate-spin text-teal-600 mx-auto mb-2" />
              <p className="text-xs text-slate-500">Loading share links...</p>
            </div>
          ) : links.length === 0 ? (
            <div className="p-10 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 space-y-2">
              <Share2 className="w-10 h-10 text-slate-300 dark:text-slate-600 mx-auto" />
              <p className="text-xs text-slate-500 font-medium">No active sharing links generated yet.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {links.map((link) => {
                const isExpired = new Date(link.expires_at) < new Date();
                const statusText = !link.is_active ? 'Revoked' : isExpired ? 'Expired' : 'Active';
                return (
                  <div
                    key={link.id}
                    className={`p-4 rounded-2xl bg-white dark:bg-slate-900 border transition-all space-y-3 ${
                      link.is_active && !isExpired
                        ? 'border-slate-200/90 dark:border-slate-800 shadow-2xs'
                        : 'border-slate-100 dark:border-slate-800/60 opacity-65 bg-slate-50/50'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center space-x-2">
                          <h4 className="text-xs font-bold text-slate-900 dark:text-white">
                            {link.recipient_name || link.title}
                          </h4>
                          <span
                            className={`text-[9px] font-bold uppercase px-2 py-0.5 rounded-md ${
                              statusText === 'Active'
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                : statusText === 'Revoked'
                                ? 'bg-rose-50 text-rose-700 border border-rose-200'
                                : 'bg-slate-100 text-slate-500 border border-slate-200'
                            }`}
                          >
                            {statusText}
                          </span>
                          <span className="text-[9px] font-bold uppercase px-2 py-0.5 rounded-md bg-teal-50 text-teal-700 border border-teal-200">
                            {link.permission || 'READ ONLY'}
                          </span>
                          {link.is_pin_protected && (
                            <span className="text-[9px] font-bold uppercase px-2 py-0.5 rounded-md bg-amber-50 text-amber-700 border border-amber-200 flex items-center space-x-1">
                              <Lock className="w-2.5 h-2.5" />
                              <span>PIN Protected</span>
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-500 mt-1 font-medium">
                          Shared Records: <strong>{link.document_ids_json?.length || 0} documents</strong> • Views: {link.access_count} / {link.max_access_count}
                        </p>
                      </div>

                      <div className="flex items-center space-x-1.5">
                        {link.is_active && !isExpired && (
                          <button
                            onClick={() => handleCopyLink(link.token)}
                            className="px-2.5 py-1 text-xs font-bold rounded-lg bg-teal-50 hover:bg-teal-100 text-teal-700 transition-colors flex items-center space-x-1 cursor-pointer"
                          >
                            {copiedToken === link.token ? (
                              <>
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
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

                        {link.is_active && !isExpired && (
                          <button
                            onClick={() => handleRevoke(link.id)}
                            className="px-2 py-1 text-xs font-bold rounded-lg text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors cursor-pointer"
                            title="Revoke Access"
                          >
                            Revoke
                          </button>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center space-x-4 text-[10px] text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-800 font-medium">
                      <span>Expires: <strong>{new Date(link.expires_at).toLocaleString()}</strong></span>
                      {link.revoked_at && (
                        <span className="text-rose-500">Revoked at: {new Date(link.revoked_at).toLocaleString()}</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SharingPage;
