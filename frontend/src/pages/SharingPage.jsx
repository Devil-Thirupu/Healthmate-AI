import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../services/api';
import { accessGrantsApi, doctorsApi } from '../services/doctorsApi';
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
  ShieldAlert,
  Stethoscope,
  Plus,
  RefreshCw,
  X,
  Heart,
  Eye,
  Shield
} from 'lucide-react';

const EXPIRY_OPTIONS = [
  { label: '1 Hour', hours: 1 },
  { label: '6 Hours', hours: 6 },
  { label: '24 Hours (1 Day)', hours: 24 },
  { label: '3 Days (72 Hours)', hours: 72 },
  { label: '7 Days (1 Week)', hours: 168 },
];

const DOCTOR_CATEGORIES = [
  { key: 'share_blood_type',          label: 'Blood Type',          icon: Activity,   desc: 'Your blood group' },
  { key: 'share_age',                 label: 'Age',                 icon: User,       desc: 'Your date of birth / age' },
  { key: 'share_current_medications', label: 'Current Medications', icon: Pill,       desc: 'Active medications from prescriptions' },
  { key: 'share_prescriptions',       label: 'Prescriptions',       icon: FileText,   desc: 'All uploaded prescription records' },
  { key: 'share_lab_reports',         label: 'Lab Reports',         icon: FlaskConical, desc: 'Blood tests & other lab results' },
  { key: 'share_vital_records',       label: 'Vital Records',       icon: Heart,      desc: 'BP, pulse, weight, glucose, etc.' },
  { key: 'share_medical_documents',   label: 'Medical Documents',   icon: FileText,   desc: 'Scans, reports, and uploads' },
  { key: 'share_health_timeline',     label: 'Health Timeline',     icon: Activity,   desc: 'Historical health events' },
  { key: 'share_ai_health_summary',   label: 'AI Health Summary',   icon: Shield,     desc: 'AI-generated health overview' },
  { key: 'share_appointment_summaries', label: 'Appointment Summaries', icon: CheckCircle2, desc: 'Previous appointment notes' },
];

const DOCTOR_DURATION_OPTIONS = [
  { value: 24,   label: '24 Hours' },
  { value: 168,  label: '7 Days' },
  { value: 720,  label: '30 Days' },
  { value: 2160, label: '90 Days' },
  { value: 8760, label: '1 Year' },
];

// Modal for creating doctor access grant
const CreateDoctorGrantModal = ({ doctors, onClose, onSave }) => {
  const [step, setStep] = useState(1);
  const [selectedDoctor, setSelectedDoctor] = useState(null);
  const [permissions, setPermissions] = useState(
    Object.fromEntries(DOCTOR_CATEGORIES.map(c => [c.key, false]))
  );
  const [allowDownload, setAllowDownload] = useState(false);
  const [duration, setDuration] = useState(168);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const connectedDoctors = doctors.filter(d => d.connection_status === 'accepted');
  const selectedCount = Object.values(permissions).filter(Boolean).length;

  const toggleAll = () => {
    const allTrue = selectedCount === DOCTOR_CATEGORIES.length;
    setPermissions(Object.fromEntries(DOCTOR_CATEGORIES.map(c => [c.key, !allTrue])));
  };

  const handleCreate = async () => {
    if (!selectedDoctor) { setError('Please select a connected doctor.'); return; }
    if (selectedCount === 0) { setError('Select at least one record category to share.'); return; }
    setSaving(true); setError('');
    try {
      await accessGrantsApi.create({
        doctor_id: selectedDoctor.id,
        ...permissions,
        allow_download: allowDownload,
        duration_hours: duration,
      });
      onSave();
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to create access grant.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
      <div className="w-full max-w-lg bg-white dark:bg-slate-900 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        <div className="flex items-center justify-between p-5 border-b border-slate-100 dark:border-slate-800">
          <div>
            <h2 className="text-sm font-bold text-slate-900 dark:text-white">Share Medical Records with Doctor</h2>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Step {step} of 2 — {step === 1 ? 'Choose Doctor' : 'Choose What to Share'}
            </p>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition">
            <X className="w-4 h-4 text-slate-500" />
          </button>
        </div>

        <div className="mx-5 mt-4 flex items-start gap-2 p-3 bg-teal-50 dark:bg-teal-950/30 border border-teal-200 dark:border-teal-800 rounded-xl">
          <Lock className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
          <p className="text-[11px] text-teal-700 dark:text-teal-400 leading-relaxed">
            <strong>Privacy first.</strong> Only the categories you explicitly select will be accessible. Records are private by default.
          </p>
        </div>

        <div className="overflow-y-auto flex-1 p-5 space-y-4">
          {error && (
            <div className="px-3 py-2 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-lg text-xs text-red-700 dark:text-red-400">{error}</div>
          )}

          {step === 1 && (
            <div className="space-y-3">
              <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">Select a connected doctor:</p>
              {connectedDoctors.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-xs">
                  No accepted doctor connections yet. Connect with a doctor in <strong>My Doctors</strong> first.
                </div>
              ) : (
                <div className="space-y-2">
                  {connectedDoctors.map(doc => (
                    <button
                      key={doc.id}
                      onClick={() => setSelectedDoctor(doc)}
                      className={`w-full text-left p-3.5 rounded-xl border transition flex items-center justify-between ${
                        selectedDoctor?.id === doc.id
                          ? 'border-teal-500 bg-teal-50/50 dark:bg-teal-950/40'
                          : 'border-slate-200 dark:border-slate-700 hover:border-slate-300'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-xl bg-teal-100 dark:bg-teal-900/60 flex items-center justify-center font-bold text-teal-700 dark:text-teal-300 text-xs">
                          {doc.full_name?.split(' ').map(n => n[0]).join('').slice(0, 2) || 'Dr'}
                        </div>
                        <div>
                          <p className="text-xs font-bold text-slate-900 dark:text-white">{doc.full_name}</p>
                          <p className="text-[10px] text-slate-500">{doc.specialty || 'General Practitioner'} • {doc.hospital_affiliation || 'Independent'}</p>
                        </div>
                      </div>
                      {selectedDoctor?.id === doc.id && (
                        <CheckCircle2 className="w-4 h-4 text-teal-600 shrink-0" />
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Sharing with <span className="text-teal-600 font-bold">{selectedDoctor?.full_name}</span>
                </p>
                <button onClick={toggleAll} className="text-[11px] text-teal-600 hover:underline font-medium">
                  {selectedCount === DOCTOR_CATEGORIES.length ? 'Deselect All' : 'Select All'}
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {DOCTOR_CATEGORIES.map(cat => {
                  const Icon = cat.icon;
                  const active = permissions[cat.key];
                  return (
                    <button
                      key={cat.key}
                      onClick={() => setPermissions(p => ({ ...p, [cat.key]: !p[cat.key] }))}
                      className={`p-3 rounded-xl border text-left transition flex items-start gap-2.5 ${
                        active
                          ? 'border-teal-500 bg-teal-50/40 dark:bg-teal-950/30'
                          : 'border-slate-200 dark:border-slate-700 hover:border-slate-300'
                      }`}
                    >
                      <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${active ? 'text-teal-600' : 'text-slate-400'}`} />
                      <div>
                        <p className={`text-xs font-bold ${active ? 'text-teal-900 dark:text-teal-200' : 'text-slate-800 dark:text-slate-200'}`}>
                          {cat.label}
                        </p>
                        <p className="text-[10px] text-slate-400">{cat.desc}</p>
                      </div>
                    </button>
                  );
                })}
              </div>

              <div className="pt-2 border-t border-slate-100 dark:border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Access Duration</label>
                  <select
                    value={duration}
                    onChange={e => setDuration(Number(e.target.value))}
                    className="text-xs border border-slate-200 dark:border-slate-700 rounded-lg px-2.5 py-1.5 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200"
                  >
                    {DOCTOR_DURATION_OPTIONS.map(d => (
                      <option key={d.value} value={d.value}>{d.label}</option>
                    ))}
                  </select>
                </div>

                <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-700 dark:text-slate-300">
                  <input
                    type="checkbox"
                    checked={allowDownload}
                    onChange={e => setAllowDownload(e.target.checked)}
                    className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  <span>Allow doctor to download original document PDFs</span>
                </label>
              </div>
            </div>
          )}
        </div>

        <div className="p-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
          {step === 2 ? (
            <button
              onClick={() => setStep(1)}
              className="px-4 py-2 text-xs text-slate-600 hover:text-slate-900 transition"
            >
              Back
            </button>
          ) : <div />}

          <div className="flex items-center gap-2">
            <button onClick={onClose} className="px-4 py-2 text-xs border border-slate-200 dark:border-slate-700 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition">
              Cancel
            </button>
            {step === 1 ? (
              <button
                disabled={!selectedDoctor}
                onClick={() => setStep(2)}
                className="px-5 py-2 text-xs font-bold bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white rounded-xl transition"
              >
                Next: Select Records
              </button>
            ) : (
              <button
                disabled={saving || selectedCount === 0}
                onClick={handleCreate}
                className="px-5 py-2 text-xs font-bold bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white rounded-xl transition flex items-center gap-1.5"
              >
                {saving && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>Grant Doctor Access</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const SharingPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialTab = searchParams.get('tab') === 'doctors' ? 'doctors' : 'links';
  const [activeTab, setActiveTab] = useState(initialTab);

  // Link Sharing state
  const [links, setLinks] = useState([]);
  const [userDocs, setUserDocs] = useState([]);
  const [isLoadingLinks, setIsLoadingLinks] = useState(true);
  const [isCreatingLink, setIsCreatingLink] = useState(false);
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

  // Doctor Grants state
  const [grants, setGrants] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [isLoadingGrants, setIsLoadingGrants] = useState(true);
  const [showDoctorModal, setShowDoctorModal] = useState(false);
  const [grantActionLoading, setGrantActionLoading] = useState(null);

  const fetchLinkData = async () => {
    try {
      setIsLoadingLinks(true);
      const [linksRes, docsRes] = await Promise.allSettled([
        api.get('/sharing/my-links'),
        api.get('/documents/'),
      ]);

      if (linksRes.status === 'fulfilled') setLinks(linksRes.value.data || []);
      if (docsRes.status === 'fulfilled') {
        const docs = docsRes.value.data || [];
        setUserDocs(docs);
        if (docs.length > 0 && formData.selected_doc_ids.length === 0) {
          setFormData((prev) => ({
            ...prev,
            selected_doc_ids: [docs[0].id]
          }));
        }
      }
    } catch (err) {
      console.error('Failed to load sharing resources:', err);
    } finally {
      setIsLoadingLinks(false);
    }
  };

  const fetchDoctorData = useCallback(async () => {
    try {
      setIsLoadingGrants(true);
      const [grantsRes, docsRes] = await Promise.allSettled([
        accessGrantsApi.list(),
        doctorsApi.list()
      ]);
      if (grantsRes.status === 'fulfilled') setGrants(grantsRes.value.data || []);
      if (docsRes.status === 'fulfilled') setDoctors(docsRes.value.data || []);
    } catch (err) {
      console.error('Failed to load doctor sharing resources:', err);
    } finally {
      setIsLoadingGrants(false);
    }
  }, []);

  useEffect(() => {
    fetchLinkData();
    fetchDoctorData();
  }, [fetchDoctorData]);

  const handleTabSwitch = (tab) => {
    setActiveTab(tab);
    setSearchParams(tab === 'doctors' ? { tab: 'doctors' } : {});
  };

  // Secure Links Handlers
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

  const handleCreateLink = async (e) => {
    e.preventDefault();
    if (formData.selected_doc_ids.length === 0) {
      alert('Please select at least one medical document or record to share.');
      return;
    }

    try {
      setIsCreatingLink(true);
      const payload = {
        title: formData.title,
        recipient_name: formData.recipient_name || 'Consulting Physician',
        duration_hours: Number(formData.duration_hours),
        permission: formData.permission,
        is_pin_protected: formData.is_pin_protected,
        pin: formData.is_pin_protected ? formData.pin : null,
        max_access_count: Number(formData.max_access_count),
        selected_document_ids: formData.selected_doc_ids,
        selected_lab_ids: formData.selected_lab_ids,
        selected_prescription_ids: formData.selected_rx_ids,
        allow_download: formData.allow_download,
        allow_ai_summary: formData.allow_ai_summary
      };

      const res = await api.post('/sharing/create', payload);
      setLinks((prev) => [res.data, ...prev]);
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
        allow_ai_summary: true
      });
    } catch (err) {
      console.error('Failed to create share link:', err);
      alert(err.response?.data?.detail || 'Failed to generate secure share link.');
    } finally {
      setIsCreatingLink(false);
    }
  };

  const handleRevokeLink = async (linkId) => {
    if (!window.confirm('Revoke this link immediately? The recipient will lose access.')) return;
    try {
      await api.delete(`/sharing/${linkId}`);
      setLinks((prev) => prev.map((l) => (l.id === linkId ? { ...l, is_active: false } : l)));
    } catch (err) {
      console.error('Failed to revoke link:', err);
    }
  };

  const copyShareUrl = (token) => {
    const origin = window.location.origin;
    const base = import.meta.env.BASE_URL || '/';
    const cleanBase = base.endsWith('/') ? base : `${base}/`;
    const shareUrl = `${origin}${cleanBase}share/${token}`;
    navigator.clipboard.writeText(shareUrl);
    setCopiedToken(token);
    setTimeout(() => setCopiedToken(null), 3000);
  };

  // Doctor Grants Handlers
  const handleRevokeDoctorGrant = async (grantId) => {
    if (!window.confirm('Revoke this doctor access grant immediately?')) return;
    setGrantActionLoading(grantId);
    try {
      await accessGrantsApi.revoke(grantId);
      setGrants(prev => prev.map(g => (g.id === grantId ? { ...g, is_active: false } : g)));
    } catch (err) {
      console.error('Failed to revoke doctor access grant:', err);
    } finally {
      setGrantActionLoading(null);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-teal-700 bg-teal-50 dark:bg-teal-950/60 px-2.5 py-0.5 rounded-full border border-teal-200/60 dark:border-teal-800/50">
              EHR Access Control
            </span>
            <span className="text-xs text-slate-400">• HIPAA Privacy Guard Active</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white font-heading tracking-tight mt-1">
            Doctor & Secure Sharing
          </h1>
          <p className="text-xs text-slate-500">
            Share temporary read-only access links or grant verified permissions directly to your connected doctors.
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center p-1 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-2xs self-start sm:self-auto">
          <button
            onClick={() => handleTabSwitch('links')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
              activeTab === 'links'
                ? 'bg-teal-600 text-white shadow-xs'
                : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Share2 className="w-3.5 h-3.5" />
            <span>Secure Share Links ({links.filter(l => l.is_active).length})</span>
          </button>
          <button
            onClick={() => handleTabSwitch('doctors')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
              activeTab === 'doctors'
                ? 'bg-teal-600 text-white shadow-xs'
                : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Stethoscope className="w-3.5 h-3.5" />
            <span>Doctor Access Grants ({grants.filter(g => g.is_active && !g.is_expired).length})</span>
          </button>
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          TAB 1: SECURE SHARE LINKS
      ───────────────────────────────────────────────────────────── */}
      {activeTab === 'links' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Create Link Form */}
          <div className="lg:col-span-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 p-5 shadow-2xs space-y-4">
            <div className="flex items-center space-x-2.5 pb-2 border-b border-slate-100 dark:border-slate-800">
              <div className="w-8 h-8 rounded-xl bg-teal-50 dark:bg-teal-950 text-teal-600 flex items-center justify-center">
                <PlusCircle className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white font-heading">
                  Create Time-Limited Share Link
                </h3>
                <p className="text-[11px] text-slate-400">Zero-knowledge PIN protection with audit logging</p>
              </div>
            </div>

            <form onSubmit={handleCreateLink} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-bold mb-1">
                  Recipient Description / Doctor Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.recipient_name}
                  onChange={(e) => setFormData({ ...formData, recipient_name: e.target.value })}
                  placeholder="e.g. Dr. Jennifer Davis (Cardiologist)"
                  className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:border-teal-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-700 dark:text-slate-300 font-bold mb-1">
                    Link Expiry Duration
                  </label>
                  <select
                    value={formData.duration_hours}
                    onChange={(e) => setFormData({ ...formData, duration_hours: Number(e.target.value) })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:border-teal-500 text-xs"
                  >
                    {EXPIRY_OPTIONS.map((opt) => (
                      <option key={opt.hours} value={opt.hours}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-700 dark:text-slate-300 font-bold mb-1">
                    Max Access Limit
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={formData.max_access_count}
                    onChange={(e) => setFormData({ ...formData, max_access_count: Number(e.target.value) })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:border-teal-500"
                  />
                </div>
              </div>

              {/* PIN Protection */}
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200/80 dark:border-slate-700 space-y-2">
                <label className="flex items-center space-x-2 cursor-pointer font-bold text-slate-800 dark:text-slate-200">
                  <input
                    type="checkbox"
                    checked={formData.is_pin_protected}
                    onChange={(e) => setFormData({ ...formData, is_pin_protected: e.target.checked })}
                    className="rounded text-teal-600 focus:ring-teal-500"
                  />
                  <span>Require 4-Digit Access PIN</span>
                </label>
                {formData.is_pin_protected && (
                  <input
                    type="password"
                    maxLength={4}
                    required
                    value={formData.pin}
                    onChange={(e) => setFormData({ ...formData, pin: e.target.value })}
                    placeholder="Enter 4-digit PIN (e.g. 7421)"
                    className="w-full px-3 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 font-mono text-center tracking-widest text-sm"
                  />
                )}
              </div>

              {/* Document Selection */}
              <div>
                <label className="block text-slate-700 dark:text-slate-300 font-bold mb-1">
                  Select Documents to Include ({formData.selected_doc_ids.length})
                </label>
                <div className="max-h-40 overflow-y-auto space-y-1.5 p-2 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
                  {userDocs.length === 0 ? (
                    <p className="text-[11px] text-slate-400 p-2 text-center">No documents in vault yet</p>
                  ) : (
                    userDocs.map((doc) => {
                      const isSelected = formData.selected_doc_ids.includes(doc.id);
                      return (
                        <div
                          key={doc.id}
                          onClick={() => handleToggleDoc(doc.id)}
                          className={`p-2 rounded-lg flex items-center justify-between cursor-pointer text-[11px] transition-colors ${
                            isSelected
                              ? 'bg-teal-50 dark:bg-teal-950 text-teal-900 dark:text-teal-200 border border-teal-200 dark:border-teal-800'
                              : 'hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300'
                          }`}
                        >
                          <div className="flex items-center space-x-2 truncate">
                            <FileText className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                            <span className="font-semibold truncate">{doc.title}</span>
                          </div>
                          <span className="text-[10px] text-slate-400 shrink-0">{doc.document_date}</span>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>

              <button
                type="submit"
                disabled={isCreatingLink || formData.selected_doc_ids.length === 0}
                className="w-full py-2.5 bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white font-bold rounded-xl shadow-xs transition-all flex items-center justify-center space-x-2"
              >
                {isCreatingLink ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <Share2 className="w-4 h-4" />
                    <span>Generate Secure Share Link</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Active Links List */}
          <div className="lg:col-span-7 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 p-5 shadow-2xs space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-teal-600" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white font-heading">
                  Active Share Links ({links.length})
                </h3>
              </div>
              <button onClick={fetchLinkData} className="text-xs text-teal-600 hover:underline flex items-center space-x-1">
                <RefreshCw className="w-3 h-3" />
                <span>Refresh</span>
              </button>
            </div>

            {isLoadingLinks ? (
              <div className="py-12 flex flex-col items-center justify-center space-y-2 text-slate-400">
                <Loader2 className="w-6 h-6 animate-spin text-teal-600" />
                <p className="text-xs">Loading secure links...</p>
              </div>
            ) : links.length === 0 ? (
              <div className="py-12 text-center text-slate-400 space-y-2">
                <Share2 className="w-8 h-8 mx-auto text-slate-300 dark:text-slate-700" />
                <p className="text-xs font-bold">No active share links</p>
                <p className="text-[11px]">Generate your first time-limited link to share records securely.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {links.map((link) => (
                  <div
                    key={link.id}
                    className={`p-4 rounded-xl border transition-all ${
                      link.is_active
                        ? 'bg-slate-50/60 dark:bg-slate-800/40 border-slate-200/80 dark:border-slate-700'
                        : 'bg-slate-100/40 dark:bg-slate-900 border-slate-200/40 opacity-60'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-bold text-slate-900 dark:text-white">
                            {link.recipient_name || 'Consulting Physician'}
                          </span>
                          {link.is_active ? (
                            <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                              Active
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                              Revoked / Expired
                            </span>
                          )}
                          {link.is_pin_protected && (
                            <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-amber-50 text-amber-700 border border-amber-200 flex items-center space-x-0.5">
                              <Lock className="w-2.5 h-2.5" />
                              <span>PIN Protected</span>
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-400 mt-0.5">
                          Expires: {new Date(link.expires_at).toLocaleString()} • Views: {link.access_count}/{link.max_access_count || '∞'}
                        </p>
                      </div>

                      {link.is_active && (
                        <div className="flex items-center space-x-1.5 shrink-0">
                          <button
                            onClick={() => copyShareUrl(link.token)}
                            className="p-1.5 rounded-lg bg-teal-50 hover:bg-teal-100 text-teal-700 text-xs font-bold transition-colors flex items-center space-x-1"
                            title="Copy link"
                          >
                            {copiedToken === link.token ? (
                              <>
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                                <span className="text-[10px] text-emerald-700">Copied!</span>
                              </>
                            ) : (
                              <>
                                <Copy className="w-3.5 h-3.5" />
                                <span className="text-[10px]">Copy Link</span>
                              </>
                            )}
                          </button>
                          <button
                            onClick={() => handleRevokeLink(link.id)}
                            className="p-1.5 rounded-lg hover:bg-rose-50 text-rose-600 text-xs transition-colors"
                            title="Revoke link"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────
          TAB 2: DOCTOR ACCESS GRANTS
      ───────────────────────────────────────────────────────────── */}
      {activeTab === 'doctors' && (
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 p-6 shadow-2xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
            <div>
              <div className="flex items-center space-x-2">
                <Stethoscope className="w-4 h-4 text-teal-600" />
                <h3 className="text-base font-bold text-slate-900 dark:text-white font-heading">
                  Verified Doctor Access Grants
                </h3>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Grant authenticated doctors access to specific clinical record categories with automatic expiry.
              </p>
            </div>
            <button
              onClick={() => setShowDoctorModal(true)}
              className="inline-flex items-center space-x-2 px-4 py-2.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl shadow-xs transition-all self-start sm:self-auto"
            >
              <Plus className="w-4 h-4" />
              <span>+ Grant Doctor Access</span>
            </button>
          </div>

          {isLoadingGrants ? (
            <div className="py-12 flex flex-col items-center justify-center space-y-2 text-slate-400">
              <Loader2 className="w-6 h-6 animate-spin text-teal-600" />
              <p className="text-xs">Loading doctor access grants...</p>
            </div>
          ) : grants.length === 0 ? (
            <div className="py-12 text-center text-slate-400 space-y-2">
              <Lock className="w-8 h-8 mx-auto text-slate-300 dark:text-slate-700" />
              <p className="text-xs font-bold">No active doctor access grants</p>
              <p className="text-[11px]">Grant verified access to your connected doctors for consultation prep.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {grants.map((grant) => {
                const isGrantActive = grant.is_active && !grant.is_expired;
                const sharedCats = DOCTOR_CATEGORIES.filter(c => grant[c.key]);

                return (
                  <div
                    key={grant.id}
                    className={`p-5 rounded-2xl border transition-all space-y-3 ${
                      isGrantActive
                        ? 'bg-slate-50/70 dark:bg-slate-800/40 border-slate-200/90 dark:border-slate-700'
                        : 'bg-slate-100/40 dark:bg-slate-900 border-slate-200/40 opacity-60'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4 flex-wrap">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-900/60 flex items-center justify-center text-teal-700 dark:text-teal-300 font-bold text-sm">
                          {grant.doctor_name?.split(' ').map(n => n[0]).join('').slice(0, 2) || 'Dr'}
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <h4 className="text-xs font-bold text-slate-900 dark:text-white">
                              {grant.doctor_name || 'Dr. Specialist'}
                            </h4>
                            {isGrantActive ? (
                              <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                Active Grant
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                                {grant.is_expired ? 'Expired' : 'Revoked'}
                              </span>
                            )}
                          </div>
                          <p className="text-[11px] text-slate-400 mt-0.5">
                            {grant.doctor_specialty || 'Physician'} • Expires: {new Date(grant.expires_at).toLocaleString()}
                          </p>
                        </div>
                      </div>

                      {isGrantActive && (
                        <button
                          onClick={() => handleRevokeDoctorGrant(grant.id)}
                          disabled={grantActionLoading === grant.id}
                          className="px-3 py-1.5 rounded-xl border border-rose-200 dark:border-rose-900 text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 text-xs font-bold transition flex items-center space-x-1"
                        >
                          {grantActionLoading === grant.id ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <>
                              <Trash2 className="w-3.5 h-3.5" />
                              <span>Revoke Access</span>
                            </>
                          )}
                        </button>
                      )}
                    </div>

                    {/* Shared categories pills */}
                    <div className="pt-2 border-t border-slate-200/60 dark:border-slate-700/60">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
                        Shared Record Categories ({sharedCats.length}):
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {sharedCats.map((cat) => {
                          const Icon = cat.icon;
                          return (
                            <span
                              key={cat.key}
                              className="px-2.5 py-1 rounded-lg text-[10px] font-semibold bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 flex items-center space-x-1"
                            >
                              <Icon className="w-3 h-3 text-teal-600" />
                              <span>{cat.label}</span>
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Doctor Grant Modal */}
      {showDoctorModal && (
        <CreateDoctorGrantModal
          doctors={doctors}
          onClose={() => setShowDoctorModal(false)}
          onSave={() => {
            setShowDoctorModal(false);
            fetchDoctorData();
          }}
        />
      )}
    </div>
  );
};

export default SharingPage;
