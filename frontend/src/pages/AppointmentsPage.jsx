import React, { useState, useEffect, useCallback } from 'react';
import {
  Calendar, Clock, Building2, CheckCircle2, XCircle,
  AlertCircle, RefreshCw, Loader2, X, Stethoscope, Info,
  Phone, MessageSquare
} from 'lucide-react';
import { appointmentsApi } from '../services/doctorsApi';

const STATUS_CONFIG = {
  pending: {
    label: 'Pending Confirmation',
    icon: AlertCircle,
    color: 'text-amber-600 bg-amber-50 border-amber-200 dark:bg-amber-950/40 dark:border-amber-800 dark:text-amber-400',
    dot: 'bg-amber-400',
  },
  accepted: {
    label: 'Confirmed',
    icon: CheckCircle2,
    color: 'text-emerald-600 bg-emerald-50 border-emerald-200 dark:bg-emerald-950/40 dark:border-emerald-800 dark:text-emerald-400',
    dot: 'bg-emerald-400',
  },
  rejected: {
    label: 'Rejected',
    icon: XCircle,
    color: 'text-red-600 bg-red-50 border-red-200 dark:bg-red-950/40 dark:border-red-800 dark:text-red-400',
    dot: 'bg-red-400',
  },
  reschedule_requested: {
    label: 'Reschedule Requested',
    icon: RefreshCw,
    color: 'text-indigo-600 bg-indigo-50 border-indigo-200 dark:bg-indigo-950/40 dark:border-indigo-800 dark:text-indigo-400',
    dot: 'bg-indigo-400',
  },
  completed: {
    label: 'Completed',
    icon: CheckCircle2,
    color: 'text-slate-600 bg-slate-50 border-slate-200 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-400',
    dot: 'bg-slate-400',
  },
  cancelled: {
    label: 'Cancelled',
    icon: X,
    color: 'text-slate-400 bg-slate-50 border-slate-200 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-500',
    dot: 'bg-slate-300',
  },
};

const TABS = [
  { key: null, label: 'All' },
  { key: 'pending', label: 'Upcoming' },
  { key: 'accepted', label: 'Confirmed' },
  { key: 'completed', label: 'Completed' },
  { key: 'cancelled', label: 'Cancelled' },
];

const ConsultationIcon = ({ type }) => {
  const icons = { video: '🎥', phone: '📞', in_person: '🏥', home_visit: '🏠' };
  return <span className="text-xs">{icons[type] || '🏥'}</span>;
};

const AppointmentCard = ({ appt, onCancel }) => {
  const s = STATUS_CONFIG[appt.status] || STATUS_CONFIG.pending;
  const Icon = s.icon;
  const [cancelling, setCancelling] = useState(false);

  const handleCancel = async () => {
    if (!window.confirm('Cancel this appointment request?')) return;
    setCancelling(true);
    try {
      await appointmentsApi.cancel(appt.id);
      onCancel();
    } catch (e) {
      alert(e.response?.data?.detail || 'Failed to cancel.');
    } finally {
      setCancelling(false);
    }
  };

  const dateStr = appt.confirmed_date || appt.requested_date;
  const timeStr = appt.confirmed_time || appt.requested_time;

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 hover:shadow-md transition-all">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-600 to-emerald-500 flex items-center justify-center text-white font-bold text-sm shrink-0">
            {appt.doctor?.name?.charAt(0) || 'D'}
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white leading-tight">
              {appt.doctor?.name || `Doctor #${appt.doctor_id}`}
            </h3>
            {appt.doctor?.specialization && (
              <p className="text-[11px] text-teal-600 dark:text-teal-400">{appt.doctor.specialization}</p>
            )}
          </div>
        </div>
        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full border text-[10px] font-semibold ${s.color}`}>
          <Icon className="w-3 h-3" /> {s.label}
        </span>
      </div>

      {/* Details */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-slate-50 dark:bg-slate-800/60 rounded-xl p-3">
          <p className="text-[10px] text-slate-400 mb-0.5 font-medium uppercase tracking-wide">Date</p>
          <p className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5 text-teal-500" />
            {dateStr || 'Not specified'}
          </p>
          {appt.status === 'pending' && appt.confirmed_date !== appt.requested_date && appt.requested_date && (
            <p className="text-[10px] text-slate-400 mt-0.5">Requested: {appt.requested_date}</p>
          )}
        </div>
        <div className="bg-slate-50 dark:bg-slate-800/60 rounded-xl p-3">
          <p className="text-[10px] text-slate-400 mb-0.5 font-medium uppercase tracking-wide">Time</p>
          <p className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1">
            <Clock className="w-3.5 h-3.5 text-teal-500" />
            {timeStr || 'Not specified'}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4 mb-3">
        <div className="flex items-center gap-1.5 text-[11px] text-slate-500 dark:text-slate-400">
          <ConsultationIcon type={appt.consultation_type} />
          <span className="capitalize">{(appt.consultation_type || 'in_person').replace('_', ' ')}</span>
        </div>
        {appt.doctor?.hospital_or_clinic && (
          <div className="flex items-center gap-1 text-[11px] text-slate-400">
            <Building2 className="w-3.5 h-3.5" /> {appt.doctor.hospital_or_clinic}
          </div>
        )}
      </div>

      {appt.reason && (
        <p className="text-[11px] text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/50 rounded-lg px-3 py-2 mb-3">
          <strong className="text-slate-700 dark:text-slate-300">Reason:</strong> {appt.reason}
        </p>
      )}

      {appt.doctor_note && (
        <div className="flex items-start gap-2 p-3 bg-teal-50 dark:bg-teal-950/30 border border-teal-200 dark:border-teal-800 rounded-lg mb-3">
          <MessageSquare className="w-3.5 h-3.5 text-teal-600 shrink-0 mt-0.5" />
          <p className="text-[11px] text-teal-700 dark:text-teal-400"><strong>Doctor's note:</strong> {appt.doctor_note}</p>
        </div>
      )}

      {appt.status === 'pending' && (
        <div className="flex items-start gap-2 p-2.5 bg-amber-50 dark:bg-amber-950/20 border border-amber-100 dark:border-amber-900 rounded-lg mb-3">
          <Info className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
          <p className="text-[10px] text-amber-600 dark:text-amber-400">Awaiting doctor confirmation. Not yet confirmed.</p>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-3 border-t border-slate-100 dark:border-slate-800">
        <span className="text-[10px] text-slate-400">
          Requested {new Date(appt.created_at).toLocaleDateString()}
        </span>
        {(appt.status === 'pending' || appt.status === 'accepted') && (
          <button
            onClick={handleCancel}
            disabled={cancelling}
            className="flex items-center gap-1 px-3 py-1.5 text-[10px] font-semibold text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/40 rounded-lg border border-red-200 dark:border-red-800 transition disabled:opacity-50"
          >
            {cancelling ? <Loader2 className="w-3 h-3 animate-spin" /> : <X className="w-3 h-3" />}
            Cancel
          </button>
        )}
      </div>
    </div>
  );
};

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(null);

  const fetchAppointments = useCallback(async () => {
    setLoading(true);
    try {
      const res = await appointmentsApi.list(activeTab);
      setAppointments(res.data);
    } catch {
      /* silently handled */
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => { fetchAppointments(); }, [fetchAppointments]);

  const counts = TABS.reduce((acc, t) => {
    acc[t.key] = t.key === null
      ? appointments.length
      : appointments.filter(a => a.status === t.key).length;
    return acc;
  }, {});

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <Calendar className="w-6 h-6 text-teal-600" /> Appointments
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Track your appointment requests. Status updates when your doctor responds.
          </p>
        </div>
        <button
          onClick={fetchAppointments}
          className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition"
        >
          <RefreshCw className={`w-4 h-4 text-slate-500 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl overflow-x-auto">
        {TABS.map(tab => (
          <button
            key={String(tab.key)}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition whitespace-nowrap ${
              activeTab === tab.key
                ? 'bg-white dark:bg-slate-900 text-teal-700 dark:text-teal-300 shadow-sm'
                : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
            }`}
          >
            {tab.label}
            {counts[tab.key] > 0 && (
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${activeTab === tab.key ? 'bg-teal-100 dark:bg-teal-900 text-teal-700 dark:text-teal-300' : 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-400'}`}>
                {counts[tab.key]}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-teal-600" />
        </div>
      ) : appointments.length === 0 ? (
        <div className="text-center py-20">
          <Calendar className="w-12 h-12 text-slate-300 dark:text-slate-700 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-700 dark:text-slate-300">No appointments found</h3>
          <p className="text-xs text-slate-400 mt-1">
            Go to <strong>My Doctors</strong> and request an appointment with a connected doctor.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {appointments.map(a => (
            <AppointmentCard key={a.id} appt={a} onCancel={fetchAppointments} />
          ))}
        </div>
      )}
    </div>
  );
}
