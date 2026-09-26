import React, { useState, useEffect, useCallback } from 'react';
import {
  Share2, Shield, Clock, CheckCircle2, XCircle, AlertTriangle,
  RefreshCw, Loader2, X, Plus, Eye, Trash2, Info, Lock,
  User, FileText, Activity, Pill, FlaskConical, Heart
} from 'lucide-react';
import { accessGrantsApi, doctorsApi } from '../services/doctorsApi';

// ─── PERMISSION CATEGORIES ─────────────────────────────────────────────────

const CATEGORIES = [
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

const DURATION_OPTIONS = [
  { value: 24,   label: '24 Hours' },
  { value: 168,  label: '7 Days' },
  { value: 720,  label: '30 Days' },
  { value: 2160, label: '90 Days' },
  { value: 8760, label: '1 Year' },
];

// ─── CREATE GRANT MODAL ────────────────────────────────────────────────────

const CreateGrantModal = ({ doctors, onClose, onSave }) => {
  const [step, setStep] = useState(1); // 1 = pick doctor, 2 = pick permissions
  const [selectedDoctor, setSelectedDoctor] = useState(null);
  const [permissions, setPermissions] = useState(
    Object.fromEntries(CATEGORIES.map(c => [c.key, false]))
  );
  const [allowDownload, setAllowDownload] = useState(false);
  const [duration, setDuration] = useState(168);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const connectedDoctors = doctors.filter(d => d.connection_status === 'accepted');
  const selectedCount = Object.values(permissions).filter(Boolean).length;

  const toggleAll = () => {
    const allTrue = selectedCount === CATEGORIES.length;
    setPermissions(Object.fromEntries(CATEGORIES.map(c => [c.key, !allTrue])));
  };

  const handleCreate = async () => {
    if (!selectedDoctor) { setError('Select a doctor.'); return; }
    if (selectedCount === 0) { setError('Select at least one category to share.'); return; }
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg bg-white dark:bg-slate-900 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-100 dark:border-slate-800">
          <div>
            <h2 className="text-sm font-bold text-slate-900 dark:text-white">Share Medical Records</h2>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Step {step} of 2 — {step === 1 ? 'Choose Doctor' : 'Choose What to Share'}
            </p>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition">
            <X className="w-4 h-4 text-slate-500" />
          </button>
        </div>

        {/* Privacy notice */}
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

          {step === 1 ? (
            /* STEP 1: Doctor selection */
            <div className="space-y-2">
              <h3 className="text-xs font-bold text-slate-700 dark:text-slate-300">Connected Doctors</h3>
              {connectedDoctors.length === 0 ? (
                <div className="text-center py-8">
                  <Shield className="w-10 h-10 text-slate-300 dark:text-slate-700 mx-auto mb-2" />
                  <p className="text-xs text-slate-500">No connected doctors yet.</p>
                  <p className="text-[11px] text-slate-400 mt-1">Go to My Doctors to connect with a doctor first.</p>
                </div>
              ) : (
                connectedDoctors.map(d => (
                  <button
                    key={d.id}
                    onClick={() => setSelectedDoctor(d)}
                    className={`w-full flex items-center gap-3 p-3.5 rounded-xl border text-left transition ${
                      selectedDoctor?.id === d.id
                        ? 'border-teal-400 bg-teal-50 dark:bg-teal-950/30 dark:border-teal-700'
                        : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 bg-white dark:bg-slate-800/50'
                    }`}
                  >
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-teal-600 to-emerald-500 flex items-center justify-center text-white font-bold text-sm shrink-0">
                      {d.name.charAt(0)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-bold text-slate-900 dark:text-white">{d.name}</p>
                      <p className="text-[11px] text-slate-400 truncate">{d.specialization || d.hospital_or_clinic || 'Doctor'}</p>
                    </div>
                    {selectedDoctor?.id === d.id && <CheckCircle2 className="w-4 h-4 text-teal-600 shrink-0" />}
                  </button>
                ))
              )}
            </div>
          ) : (
            /* STEP 2: Permission categories */
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-700 dark:text-slate-300">Choose Categories to Share</h3>
                <button onClick={toggleAll} className="text-[11px] text-teal-600 dark:text-teal-400 font-semibold hover:underline">
                  {selectedCount === CATEGORIES.length ? 'Deselect All' : 'Select All'}
                </button>
              </div>
              <div className="grid grid-cols-1 gap-2">
                {CATEGORIES.map(cat => {
                  const Icon = cat.icon;
                  const checked = permissions[cat.key];
                  return (
                    <button
                      key={cat.key}
                      onClick={() => setPermissions(p => ({ ...p, [cat.key]: !p[cat.key] }))}
                      className={`flex items-center gap-3 p-3 rounded-xl border text-left transition ${
                        checked
                          ? 'border-teal-400 bg-teal-50 dark:bg-teal-950/30 dark:border-teal-700'
                          : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 bg-white dark:bg-slate-800/40'
                      }`}
                    >
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${checked ? 'bg-teal-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-400'}`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <div className="flex-1">
                        <p className="text-xs font-bold text-slate-900 dark:text-white">{cat.label}</p>
                        <p className="text-[10px] text-slate-400">{cat.desc}</p>
                      </div>
                      <div className={`w-4 h-4 rounded-full border-2 shrink-0 flex items-center justify-center ${checked ? 'border-teal-600 bg-teal-600' : 'border-slate-300 dark:border-slate-600'}`}>
                        {checked && <Check className="w-2.5 h-2.5 text-white" />}
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Duration & Download */}
              <div className="space-y-3 pt-2 border-t border-slate-100 dark:border-slate-800">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1.5">Access Duration</label>
                  <div className="flex flex-wrap gap-2">
                    {DURATION_OPTIONS.map(opt => (
                      <button
                        key={opt.value}
                        onClick={() => setDuration(opt.value)}
                        className={`px-3 py-1.5 text-[11px] font-semibold rounded-lg border transition ${
                          duration === opt.value
                            ? 'border-teal-500 bg-teal-600 text-white'
                            : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-teal-400'
                        }`}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={allowDownload}
                    onChange={e => setAllowDownload(e.target.checked)}
                    className="w-4 h-4 accent-teal-600"
                  />
                  <span className="text-xs text-slate-700 dark:text-slate-300">Allow doctor to download documents</span>
                </label>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-5 py-4 border-t border-slate-100 dark:border-slate-800">
          <button
            onClick={step === 1 ? onClose : () => setStep(1)}
            className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition"
          >
            {step === 1 ? 'Cancel' : '← Back'}
          </button>
          {step === 1 ? (
            <button
              onClick={() => { if (!selectedDoctor) { setError('Select a doctor to continue.'); return; } setError(''); setStep(2); }}
              disabled={!selectedDoctor}
              className="px-5 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-lg transition disabled:opacity-50"
            >
              Next →
            </button>
          ) : (
            <button
              onClick={handleCreate}
              disabled={saving || selectedCount === 0}
              className="flex items-center gap-2 px-5 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-lg transition disabled:opacity-50"
            >
              {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Share2 className="w-3.5 h-3.5" />}
              Create Access ({selectedCount} categor{selectedCount === 1 ? 'y' : 'ies'})
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// Missing import for Check icon
import { Check } from 'lucide-react';

// ─── GRANT ROW ─────────────────────────────────────────────────────────────

const GrantRow = ({ grant, onRevoke }) => {
  const now = new Date();
  const expires = new Date(grant.expires_at);
  const isExpired = expires < now;
  const isRevoked = !!grant.revoked_at;
  const isActive = grant.is_active && !isExpired && !isRevoked;

  const sharedCategories = CATEGORIES.filter(c => grant[c.key]);
  const [revoking, setRevoking] = useState(false);

  const handleRevoke = async () => {
    if (!window.confirm('Revoke this access grant? The doctor will immediately lose access.')) return;
    setRevoking(true);
    try {
      await accessGrantsApi.revoke(grant.id);
      onRevoke();
    } catch (e) {
      alert('Failed to revoke grant.');
    } finally {
      setRevoking(false);
    }
  };

  return (
    <div className={`bg-white dark:bg-slate-900 rounded-xl border p-4 transition ${isActive ? 'border-slate-200 dark:border-slate-800' : 'border-slate-100 dark:border-slate-800/50 opacity-60'}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-teal-600 to-emerald-500 flex items-center justify-center text-white font-bold text-sm shrink-0">
            {grant.doctor?.name?.charAt(0) || 'D'}
          </div>
          <div>
            <p className="text-xs font-bold text-slate-900 dark:text-white">{grant.doctor?.name || 'Doctor'}</p>
            <p className="text-[11px] text-slate-400">{grant.doctor?.specialization || ''}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isRevoked ? (
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400">Revoked</span>
          ) : isExpired ? (
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-500">Expired</span>
          ) : (
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-600 dark:text-emerald-400">Active</span>
          )}
        </div>
      </div>

      {/* Shared categories */}
      <div className="mt-3 flex flex-wrap gap-1.5">
        {sharedCategories.map(c => {
          const Icon = c.icon;
          return (
            <span key={c.key} className="flex items-center gap-1 px-2 py-0.5 bg-teal-50 dark:bg-teal-950/30 border border-teal-200 dark:border-teal-800 rounded-full text-[10px] font-semibold text-teal-700 dark:text-teal-400">
              <Icon className="w-3 h-3" /> {c.label}
            </span>
          );
        })}
        {sharedCategories.length === 0 && (
          <span className="text-[11px] text-slate-400">No categories shared</span>
        )}
      </div>

      <div className="mt-3 flex items-center justify-between">
        <div className="space-y-0.5">
          <p className="text-[10px] text-slate-400">
            <Clock className="w-3 h-3 inline mr-1" />
            Expires: {expires.toLocaleString()}
          </p>
          <p className="text-[10px] text-slate-400">
            Viewed {grant.access_count} time{grant.access_count !== 1 ? 's' : ''}
            {grant.allow_download ? ' · Download enabled' : ''}
          </p>
        </div>
        {isActive && (
          <button
            onClick={handleRevoke}
            disabled={revoking}
            className="flex items-center gap-1 px-3 py-1.5 text-[10px] font-semibold text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/40 rounded-lg border border-red-200 dark:border-red-800 transition"
          >
            {revoking ? <Loader2 className="w-3 h-3 animate-spin" /> : <Trash2 className="w-3 h-3" />}
            Revoke
          </button>
        )}
      </div>
    </div>
  );
};

// ─── MAIN PAGE ─────────────────────────────────────────────────────────────

export default function DoctorSharingPage() {
  const [grants, setGrants] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAll, setShowAll] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [g, d] = await Promise.all([
        accessGrantsApi.list(!showAll),
        doctorsApi.list(),
      ]);
      setGrants(g.data);
      setDoctors(d.data);
    } catch {
      /* handled silently */
    } finally {
      setLoading(false);
    }
  }, [showAll]);

  useEffect(() => { fetchData(); }, [fetchData]);

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <Share2 className="w-6 h-6 text-teal-600" /> Sharing Center
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Granular, time-limited record access for your doctors. You control exactly what they see.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={fetchData} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition">
            <RefreshCw className={`w-4 h-4 text-slate-500 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl transition shadow-sm"
          >
            <Plus className="w-4 h-4" /> Share Records
          </button>
        </div>
      </div>

      {/* Privacy reminder */}
      <div className="flex items-start gap-3 p-4 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl">
        <Shield className="w-5 h-5 text-teal-600 shrink-0 mt-0.5" />
        <div>
          <p className="text-xs font-bold text-slate-900 dark:text-white">Your records are private by default</p>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 leading-relaxed">
            Connecting with a doctor does <strong>not</strong> share your records. You must explicitly create an access grant and choose each category. You can revoke access at any time.
          </p>
        </div>
      </div>

      {/* Filter toggle */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setShowAll(false)}
          className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${!showAll ? 'bg-teal-600 text-white' : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800'}`}
        >
          Active Only
        </button>
        <button
          onClick={() => setShowAll(true)}
          className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition ${showAll ? 'bg-teal-600 text-white' : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800'}`}
        >
          All Grants
        </button>
      </div>

      {/* Grant list */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-teal-600" />
        </div>
      ) : grants.length === 0 ? (
        <div className="text-center py-20">
          <Share2 className="w-12 h-12 text-slate-300 dark:text-slate-700 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300">No access grants yet</h3>
          <p className="text-xs text-slate-400 mt-1">
            Click "Share Records" to create a granular access grant for a connected doctor.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {grants.map(g => <GrantRow key={g.id} grant={g} onRevoke={fetchData} />)}
        </div>
      )}

      {showCreateModal && (
        <CreateGrantModal
          doctors={doctors}
          onClose={() => setShowCreateModal(false)}
          onSave={() => { setShowCreateModal(false); fetchData(); }}
        />
      )}
    </div>
  );
}
