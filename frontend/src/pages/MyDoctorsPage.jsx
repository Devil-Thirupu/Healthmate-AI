import React, { useState, useEffect, useCallback } from 'react';
import {
  Stethoscope, Plus, Phone, Mail, MapPin, Building2,
  Clock, CheckCircle2, XCircle, AlertCircle, RefreshCw,
  Calendar, Share2, Unlink, ChevronRight, User, Search,
  Loader2, Trash2, Edit3, X, Check, Info
} from 'lucide-react';
import { doctorsApi, connectionsApi } from '../services/doctorsApi';

// ─── STATUS badge ─────────────────────────────────────────────────────────

const StatusBadge = ({ status }) => {
  const cfg = {
    pending:      { icon: AlertCircle, color: 'text-amber-600 bg-amber-50 border-amber-200 dark:bg-amber-950/40 dark:border-amber-800 dark:text-amber-400', label: 'Pending' },
    accepted:     { icon: CheckCircle2, color: 'text-emerald-600 bg-emerald-50 border-emerald-200 dark:bg-emerald-950/40 dark:border-emerald-800 dark:text-emerald-400', label: 'Connected' },
    rejected:     { icon: XCircle, color: 'text-red-600 bg-red-50 border-red-200 dark:bg-red-950/40 dark:border-red-800 dark:text-red-400', label: 'Rejected' },
    cancelled:    { icon: XCircle, color: 'text-slate-500 bg-slate-50 border-slate-200 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-400', label: 'Cancelled' },
    disconnected: { icon: Unlink, color: 'text-slate-500 bg-slate-50 border-slate-200 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-400', label: 'Disconnected' },
  };
  const c = cfg[status] || cfg.pending;
  const Icon = c.icon;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px] font-semibold ${c.color}`}>
      <Icon className="w-3 h-3" /> {c.label}
    </span>
  );
};

// ─── ADD / EDIT DOCTOR MODAL ──────────────────────────────────────────────

const DoctorFormModal = ({ doctor, onClose, onSave }) => {
  const isEdit = !!doctor;
  const [form, setForm] = useState({
    name: doctor?.name || '',
    specialization: doctor?.specialization || '',
    hospital_or_clinic: doctor?.hospital_or_clinic || '',
    phone_number: doctor?.phone_number || '',
    email: doctor?.email || '',
    address: doctor?.address || '',
    consultation_type: doctor?.consultation_type || 'in_person',
    available_days: doctor?.available_days || '',
    available_time: doctor?.available_time || '',
    notes: doctor?.notes || '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSave = async () => {
    if (!form.name.trim()) { setError('Doctor name is required.'); return; }
    setSaving(true); setError('');
    try {
      if (isEdit) {
        await doctorsApi.update(doctor.id, form);
      } else {
        await doctorsApi.create(form);
      }
      onSave();
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to save doctor profile.');
    } finally {
      setSaving(false);
    }
  };

  const Field = ({ label, name, type = 'text', placeholder = '' }) => (
    <div>
      <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">{label}</label>
      <input
        type={type}
        value={form[name]}
        onChange={e => setForm(p => ({ ...p, [name]: e.target.value }))}
        placeholder={placeholder}
        className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500 transition"
      />
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg bg-white dark:bg-slate-900 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-teal-600 flex items-center justify-center">
              <Stethoscope className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900 dark:text-white">{isEdit ? 'Edit Doctor' : 'Add New Doctor'}</h2>
              <p className="text-[11px] text-slate-500">Fill in the doctor's details</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition">
            <X className="w-4 h-4 text-slate-500" />
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto p-5 space-y-4 flex-1">
          {error && (
            <div className="px-3 py-2 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-lg text-xs text-red-700 dark:text-red-400">
              {error}
            </div>
          )}
          <Field label="Doctor Name *" name="name" placeholder="Dr. Ramachandran" />
          <div className="grid grid-cols-2 gap-3">
            <Field label="Specialization" name="specialization" placeholder="Cardiologist" />
            <Field label="Phone Number" name="phone_number" placeholder="+91 98765 43210" />
          </div>
          <Field label="Hospital / Clinic" name="hospital_or_clinic" placeholder="Apollo Hospitals, Chennai" />
          <Field label="Email" name="email" type="email" placeholder="doctor@hospital.com" />
          <Field label="Address" name="address" placeholder="Clinic address" />
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Consultation Type</label>
              <select
                value={form.consultation_type}
                onChange={e => setForm(p => ({ ...p, consultation_type: e.target.value }))}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
              >
                <option value="in_person">In Person</option>
                <option value="video">Video</option>
                <option value="phone">Phone</option>
                <option value="home_visit">Home Visit</option>
              </select>
            </div>
            <Field label="Available Days" name="available_days" placeholder="Mon, Wed, Fri" />
          </div>
          <Field label="Available Time" name="available_time" placeholder="09:00 AM – 05:00 PM" />
          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Notes (private)</label>
            <textarea
              rows={2}
              value={form.notes}
              onChange={e => setForm(p => ({ ...p, notes: e.target.value }))}
              placeholder="Any notes about this doctor..."
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500 resize-none"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-5 py-4 border-t border-slate-100 dark:border-slate-800">
          <button onClick={onClose} className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition">Cancel</button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-5 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-lg transition disabled:opacity-50"
          >
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
            {isEdit ? 'Save Changes' : 'Add Doctor'}
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── REQUEST APPOINTMENT MODAL ─────────────────────────────────────────────
import { appointmentsApi } from '../services/doctorsApi';

const AppointmentModal = ({ doctor, onClose, onSave }) => {
  const [form, setForm] = useState({
    requested_date: '',
    requested_time: '',
    consultation_type: doctor.consultation_type || 'in_person',
    reason: '',
    patient_note: '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (!form.requested_date) { setError('Please select a preferred date.'); return; }
    setSaving(true); setError('');
    try {
      await appointmentsApi.request({ ...form, doctor_id: doctor.id });
      onSave();
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to request appointment.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
      <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-2xl shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between p-5 border-b border-slate-100 dark:border-slate-800">
          <div>
            <h2 className="text-sm font-bold text-slate-900 dark:text-white">Request Appointment</h2>
            <p className="text-[11px] text-slate-500 mt-0.5">Dr. {doctor.name}</p>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition">
            <X className="w-4 h-4 text-slate-500" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {/* Important notice */}
          <div className="flex items-start gap-2 p-3 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg">
            <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <p className="text-[11px] text-amber-700 dark:text-amber-400 leading-relaxed">
              This sends a <strong>request</strong> to the doctor. Your appointment is <strong>not confirmed</strong> until the doctor accepts it.
            </p>
          </div>

          {error && (
            <div className="px-3 py-2 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-lg text-xs text-red-700 dark:text-red-400">{error}</div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Preferred Date *</label>
              <input type="date" value={form.requested_date} min={new Date().toISOString().split('T')[0]}
                onChange={e => setForm(p => ({ ...p, requested_date: e.target.value }))}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Preferred Time</label>
              <input type="time" value={form.requested_time}
                onChange={e => setForm(p => ({ ...p, requested_time: e.target.value }))}
                className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Consultation Type</label>
            <select value={form.consultation_type} onChange={e => setForm(p => ({ ...p, consultation_type: e.target.value }))}
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option value="in_person">In Person</option>
              <option value="video">Video Call</option>
              <option value="phone">Phone</option>
              <option value="home_visit">Home Visit</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Reason for Visit</label>
            <input type="text" value={form.reason} onChange={e => setForm(p => ({ ...p, reason: e.target.value }))}
              placeholder="e.g. Follow-up, Routine checkup, Lab review"
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">Additional Note</label>
            <textarea rows={2} value={form.patient_note} onChange={e => setForm(p => ({ ...p, patient_note: e.target.value }))}
              placeholder="Anything else the doctor should know..."
              className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500 resize-none"
            />
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 px-5 py-4 border-t border-slate-100 dark:border-slate-800">
          <button onClick={onClose} className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition">Cancel</button>
          <button onClick={handleSubmit} disabled={saving}
            className="flex items-center gap-2 px-5 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-lg transition disabled:opacity-50"
          >
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Calendar className="w-3.5 h-3.5" />}
            Send Request
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── DOCTOR CARD ───────────────────────────────────────────────────────────

const DoctorCard = ({ doctor, onEdit, onRequestAppointment, onShareRecords, onDisconnect, onRefresh }) => {
  const [connecting, setConnecting] = useState(false);
  const [localStatus, setLocalStatus] = useState(doctor.connection_status);

  const handleConnect = async () => {
    setConnecting(true);
    try {
      await connectionsApi.request({ doctor_id: doctor.id });
      setLocalStatus('pending');
      onRefresh();
    } catch (e) {
      alert(e.response?.data?.detail || 'Connection request failed.');
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!doctor.connection_id) return;
    if (!window.confirm(`Disconnect from Dr. ${doctor.name}? This will not delete their profile.`)) return;
    try {
      const newStatus = localStatus === 'pending' ? 'cancelled' : 'disconnected';
      await connectionsApi.update(doctor.connection_id, { status: newStatus });
      setLocalStatus(newStatus);
      onRefresh();
    } catch (e) {
      alert(e.response?.data?.detail || 'Failed to disconnect.');
    }
  };

  return (
    <div className="group bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 hover:border-teal-300 dark:hover:border-teal-700 hover:shadow-lg hover:shadow-teal-500/5 transition-all duration-200 overflow-hidden flex flex-col">
      {/* Card Header */}
      <div className="p-5 flex-1">
        <div className="flex items-start justify-between mb-3">
          {/* Avatar */}
          <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-teal-600 to-emerald-500 flex items-center justify-center text-white font-bold text-base shadow-sm shrink-0">
            {doctor.name.charAt(0).toUpperCase()}
          </div>
          {localStatus && <StatusBadge status={localStatus} />}
        </div>

        <h3 className="text-sm font-bold text-slate-900 dark:text-white leading-tight">{doctor.name}</h3>
        {doctor.specialization && (
          <p className="text-xs text-teal-600 dark:text-teal-400 font-medium mt-0.5">{doctor.specialization}</p>
        )}

        <div className="mt-3 space-y-1.5">
          {doctor.hospital_or_clinic && (
            <div className="flex items-center gap-1.5 text-[11px] text-slate-500 dark:text-slate-400">
              <Building2 className="w-3.5 h-3.5 shrink-0" /> {doctor.hospital_or_clinic}
            </div>
          )}
          {doctor.phone_number && (
            <div className="flex items-center gap-1.5 text-[11px] text-slate-500 dark:text-slate-400">
              <Phone className="w-3.5 h-3.5 shrink-0" /> {doctor.phone_number}
            </div>
          )}
          {doctor.available_time && (
            <div className="flex items-center gap-1.5 text-[11px] text-slate-500 dark:text-slate-400">
              <Clock className="w-3.5 h-3.5 shrink-0" /> {doctor.available_days ? `${doctor.available_days} · ` : ''}{doctor.available_time}
            </div>
          )}
        </div>

        {doctor.notes && (
          <p className="mt-3 text-[11px] text-slate-400 dark:text-slate-500 italic leading-relaxed line-clamp-2">
            {doctor.notes}
          </p>
        )}
      </div>

      {/* Actions */}
      <div className="px-5 pb-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex flex-wrap gap-2">
        <button
          onClick={() => onEdit(doctor)}
          className="flex items-center gap-1 px-2.5 py-1.5 text-[10px] font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition"
        >
          <Edit3 className="w-3.5 h-3.5" /> Edit
        </button>

        {(!localStatus || localStatus === 'cancelled' || localStatus === 'disconnected' || localStatus === 'rejected') && (
          <button
            onClick={handleConnect}
            disabled={connecting}
            className="flex items-center gap-1 px-2.5 py-1.5 text-[10px] font-semibold text-teal-600 dark:text-teal-400 hover:bg-teal-50 dark:hover:bg-teal-950/40 rounded-lg border border-teal-200 dark:border-teal-800 transition disabled:opacity-50"
          >
            {connecting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
            Connect
          </button>
        )}

        {localStatus === 'accepted' && (
          <>
            <button
              onClick={() => onRequestAppointment(doctor)}
              className="flex items-center gap-1 px-2.5 py-1.5 text-[10px] font-semibold text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 rounded-lg border border-indigo-200 dark:border-indigo-800 transition"
            >
              <Calendar className="w-3.5 h-3.5" /> Appointment
            </button>
            <button
              onClick={() => onShareRecords(doctor)}
              className="flex items-center gap-1 px-2.5 py-1.5 text-[10px] font-semibold text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-950/40 rounded-lg border border-purple-200 dark:border-purple-800 transition"
            >
              <Share2 className="w-3.5 h-3.5" /> Share Records
            </button>
          </>
        )}

        {(localStatus === 'pending' || localStatus === 'accepted') && (
          <button
            onClick={handleDisconnect}
            className="flex items-center gap-1 px-2.5 py-1.5 text-[10px] font-semibold text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/40 rounded-lg border border-red-200 dark:border-red-800 transition"
          >
            <Unlink className="w-3.5 h-3.5" /> Disconnect
          </button>
        )}
      </div>
    </div>
  );
};

// ─── MAIN PAGE ─────────────────────────────────────────────────────────────

export default function MyDoctorsPage() {
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editDoctor, setEditDoctor] = useState(null);
  const [appointmentDoctor, setAppointmentDoctor] = useState(null);
  const [toast, setToast] = useState(null);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  const fetchDoctors = useCallback(async () => {
    setLoading(true);
    try {
      const res = await doctorsApi.list();
      setDoctors(res.data);
    } catch {
      showToast('Failed to load doctors.', 'error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchDoctors(); }, [fetchDoctors]);

  const filtered = doctors.filter(d =>
    d.name.toLowerCase().includes(search.toLowerCase()) ||
    (d.specialization || '').toLowerCase().includes(search.toLowerCase()) ||
    (d.hospital_or_clinic || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-5 right-5 z-[9999] px-4 py-2.5 rounded-xl shadow-lg text-xs font-semibold text-white transition-all ${toast.type === 'error' ? 'bg-red-600' : 'bg-teal-600'}`}>
          {toast.msg}
        </div>
      )}

      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <Stethoscope className="w-6 h-6 text-teal-600" /> My Doctors
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Manage your healthcare team. Connections and record sharing are <strong>separate</strong> — connecting a doctor does not share your records.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={fetchDoctors} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition">
            <RefreshCw className={`w-4 h-4 text-slate-500 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => { setEditDoctor(null); setShowAddModal(true); }}
            className="flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl transition shadow-sm"
          >
            <Plus className="w-4 h-4" /> Add Doctor
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search by name, specialization, or hospital..."
          className="w-full pl-9 pr-4 py-2.5 text-sm rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500 transition"
        />
      </div>

      {/* Stats strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Total Doctors', value: doctors.length, color: 'text-slate-700 dark:text-slate-200' },
          { label: 'Connected', value: doctors.filter(d => d.connection_status === 'accepted').length, color: 'text-emerald-600 dark:text-emerald-400' },
          { label: 'Pending', value: doctors.filter(d => d.connection_status === 'pending').length, color: 'text-amber-600 dark:text-amber-400' },
          { label: 'Inactive', value: doctors.filter(d => !d.is_active).length, color: 'text-slate-400' },
        ].map(s => (
          <div key={s.label} className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 px-4 py-3">
            <p className={`text-lg font-extrabold ${s.color}`}>{s.value}</p>
            <p className="text-[10px] text-slate-500 dark:text-slate-400 font-medium">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Doctor grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-teal-600" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-20">
          <Stethoscope className="w-12 h-12 text-slate-300 dark:text-slate-700 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300">
            {search ? 'No doctors match your search' : 'No doctors added yet'}
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            {search ? 'Try a different search term.' : 'Click "Add Doctor" to add your first healthcare provider.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map(doc => (
            <DoctorCard
              key={doc.id}
              doctor={doc}
              onEdit={d => { setEditDoctor(d); setShowAddModal(true); }}
              onRequestAppointment={d => setAppointmentDoctor(d)}
              onShareRecords={d => window.location.href = `/sharing?doctor_id=${d.id}`}
              onDisconnect={() => fetchDoctors()}
              onRefresh={fetchDoctors}
            />
          ))}
        </div>
      )}

      {/* Modals */}
      {showAddModal && (
        <DoctorFormModal
          doctor={editDoctor}
          onClose={() => { setShowAddModal(false); setEditDoctor(null); }}
          onSave={() => { setShowAddModal(false); setEditDoctor(null); fetchDoctors(); showToast(editDoctor ? 'Doctor updated.' : 'Doctor added.'); }}
        />
      )}

      {appointmentDoctor && (
        <AppointmentModal
          doctor={appointmentDoctor}
          onClose={() => setAppointmentDoctor(null)}
          onSave={() => {
            setAppointmentDoctor(null);
            showToast('Appointment request sent! Awaiting doctor confirmation.');
          }}
        />
      )}
    </div>
  );
}
