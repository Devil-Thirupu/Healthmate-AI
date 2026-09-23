import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import {
  Pill,
  Sun,
  Sunrise,
  Moon,
  Clock,
  CheckCircle2,
  AlertCircle,
  FileText,
  RefreshCw,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Check
} from 'lucide-react';

const MedicationScheduleCard = ({ onOpenPrescription }) => {
  const [schedule, setSchedule] = useState({
    date: '',
    total_active_reminders: 0,
    completed_count: 0,
    remaining_count: 0,
    morning: [],
    afternoon: [],
    night: [],
    unspecified: []
  });
  const [isLoading, setIsLoading] = useState(true);

  const fetchSchedule = async () => {
    try {
      setIsLoading(true);
      const res = await api.get('/reminders/schedule');
      setSchedule(res.data);
    } catch (err) {
      console.error('Error fetching medication schedule:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSchedule();
    const handleUpdate = () => fetchSchedule();
    window.addEventListener('healthmate_reminder_updated', handleUpdate);
    window.addEventListener('healthmate_doc_uploaded', handleUpdate);
    return () => {
      window.removeEventListener('healthmate_reminder_updated', handleUpdate);
      window.removeEventListener('healthmate_doc_uploaded', handleUpdate);
    };
  }, []);

  const handleComplete = async (id) => {
    try {
      await api.post(`/reminders/${id}/complete`);
      fetchSchedule();
      window.dispatchEvent(new Event('healthmate_reminder_updated'));
    } catch (err) {
      console.error('Error completing reminder:', err);
    }
  };

  const handleSnooze = async (id) => {
    try {
      await api.post(`/reminders/${id}/snooze`, { snooze_minutes: 30 });
      fetchSchedule();
      window.dispatchEvent(new Event('healthmate_reminder_updated'));
    } catch (err) {
      console.error('Error snoozing reminder:', err);
    }
  };

  const handleSync = async () => {
    try {
      setIsLoading(true);
      await api.post('/reminders/sync');
      fetchSchedule();
      window.dispatchEvent(new Event('healthmate_reminder_updated'));
    } catch (err) {
      console.error('Error syncing reminders:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const renderSlot = (title, icon, items, defaultTime) => {
    const Icon = icon;
    if (items.length === 0) return null;

    return (
      <div className="bg-slate-50/70 dark:bg-slate-800/60 rounded-2xl p-4 border border-slate-200/80 dark:border-slate-800 space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-slate-200/60 dark:border-slate-700/60">
          <div className="flex items-center space-x-2">
            <div className="w-7 h-7 rounded-xl bg-white dark:bg-slate-800 shadow-2xs flex items-center justify-center text-teal-600">
              <Icon className="w-4 h-4" />
            </div>
            <div>
              <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider font-heading">{title}</h4>
              <p className="text-[10px] text-slate-400">{defaultTime}</p>
            </div>
          </div>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300">
            {items.filter(i => i.status === 'COMPLETED').length}/{items.length} Taken
          </span>
        </div>

        <div className="space-y-2.5">
          {items.map((item) => (
            <div
              key={item.id}
              className={`p-3 rounded-xl transition-all ${
                item.status === 'COMPLETED'
                  ? 'bg-white/60 dark:bg-slate-900/40 border border-emerald-200/60 dark:border-emerald-900/40 opacity-75'
                  : 'bg-white dark:bg-slate-800 border border-slate-200/90 dark:border-slate-700 shadow-2xs'
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-slate-900 dark:text-white">
                      {item.medicine_name}
                    </span>
                    <span className="text-[10px] font-bold text-teal-700 dark:text-teal-400 bg-teal-50 dark:bg-teal-950 px-2 py-0.5 rounded-full border border-teal-200/50">
                      {item.dosage || 'Prescribed dose'}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 mt-1 text-[11px] text-slate-500">
                    <span>{item.frequency || 'Standard'}</span>
                    <span>•</span>
                    <span>{item.timing || 'As prescribed'}</span>
                  </div>

                  {item.source_document_title && (
                    <div className="mt-1 flex items-center space-x-1.5 text-[10px] text-slate-400">
                      <FileText className="w-3 h-3 text-teal-600" />
                      <span className="truncate max-w-[200px]">Source: {item.source_document_title}</span>
                      {item.document_id && onOpenPrescription && (
                        <button
                          onClick={() => onOpenPrescription(item.document_id)}
                          className="text-teal-600 dark:text-teal-400 hover:underline font-bold inline-flex items-center ml-1"
                        >
                          [Inspect Rx]
                        </button>
                      )}
                    </div>
                  )}
                </div>

                <div className="flex items-center space-x-2 shrink-0 self-end sm:self-center">
                  {item.status === 'COMPLETED' ? (
                    <span className="inline-flex items-center space-x-1 text-[11px] font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950 px-2.5 py-1 rounded-lg border border-emerald-200/60">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Taken</span>
                    </span>
                  ) : (
                    <>
                      <button
                        onClick={() => handleSnooze(item.id)}
                        className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
                      >
                        Snooze
                      </button>
                      <button
                        onClick={() => handleComplete(item.id)}
                        className="px-3 py-1 text-xs font-bold rounded-lg bg-teal-600 hover:bg-teal-700 text-white shadow-2xs transition-all active:scale-95 flex items-center space-x-1"
                      >
                        <Check className="w-3 h-3" />
                        <span>Take Dose</span>
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const hasAnyReminders = schedule.morning.length > 0 || schedule.afternoon.length > 0 || schedule.night.length > 0 || schedule.unspecified.length > 0;

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 p-6 shadow-2xs">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 pb-4 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-teal-50 dark:bg-teal-950 text-teal-600 flex items-center justify-center">
            <Pill className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white font-heading">
                Medication Adherence & Daily Dosing Hub
              </h3>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-teal-50 text-teal-700 border border-teal-200/60">
                {schedule.completed_count} / {schedule.total_active_reminders} Logged
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Derived strictly from verified prescriptions • Non-prescribing compliance assistant
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 self-start sm:self-center">
          <button
            onClick={handleSync}
            disabled={isLoading}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-teal-700 bg-teal-50 hover:bg-teal-100 transition-colors border border-teal-200/60"
            title="Resync from prescriptions"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Sync Reminders</span>
          </button>
        </div>
      </div>

      {/* Schedule slots */}
      {!hasAnyReminders ? (
        <div className="p-8 text-center bg-slate-50 dark:bg-slate-800/40 rounded-2xl border border-dashed border-slate-200 dark:border-slate-700">
          <Pill className="w-8 h-8 mx-auto mb-2 text-slate-300" />
          <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">No active medication reminders for today</h4>
          <p className="text-xs text-slate-400 max-w-md mx-auto mt-0.5">
            Upload your doctor's prescription to automatically populate morning, afternoon, and evening medication intake schedules.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {renderSlot('Morning Doses', Sunrise, schedule.morning, '8:00 AM Slot')}
          {renderSlot('Afternoon Doses', Sun, schedule.afternoon, '1:00 PM Slot')}
          {renderSlot('Night Doses', Moon, schedule.night, '8:00 PM Slot')}
          {renderSlot('Other Scheduled', Clock, schedule.unspecified, 'Flexible Schedule')}
        </div>
      )}

      {/* Safety Guard */}
      <div className="mt-5 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700/60 flex items-start space-x-2">
        <ShieldCheck className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
        <p className="text-[11px] text-slate-500 leading-relaxed">
          <strong>Clinical Safety Guard:</strong> HealthMate AI provides schedule reminders based solely on your uploaded prescription records. It does not alter doses or substitute for medical consultation.
        </p>
      </div>
    </div>
  );
};

export default MedicationScheduleCard;
