import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import {
  Stethoscope,
  CalendarCheck,
  FileText,
  Pill,
  Activity,
  TrendingUp,
  AlertTriangle,
  HelpCircle,
  Download,
  Loader2,
  X,
  Printer,
  ChevronRight,
  ShieldCheck,
  CheckCircle2,
  Sparkles
} from 'lucide-react';

const DoctorVisitModal = ({ isOpen, onClose }) => {
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!isOpen) return;

    const fetchDoctorVisitData = async () => {
      try {
        setIsLoading(true);
        const res = await api.get('/doctor-visit');
        setData(res.data);
      } catch (err) {
        console.error('Error fetching doctor visit data:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDoctorVisitData();
  }, [isOpen]);

  if (!isOpen) return null;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="w-full max-w-3xl bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200/90 dark:border-slate-800 overflow-hidden flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="p-5 bg-teal-600 text-white flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-white/20 backdrop-blur-xs flex items-center justify-center text-white">
              <Stethoscope className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-bold font-heading">Doctor Visit Mode & Live Scribe</h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-white/20 text-white">
                  Clinical Summary Brief
                </span>
              </div>
              <p className="text-[11px] text-teal-100">
                Patient: {data?.patient_name || 'Patient'} • Consultation Date: {data?.date_of_visit || 'Today'}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handlePrint}
              className="p-2 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-semibold flex items-center space-x-1.5 transition-colors"
              title="Print Clinical Briefing Sheet"
            >
              <Printer className="w-4 h-4" />
              <span className="hidden sm:inline">Print Brief</span>
            </button>
            <button
              onClick={onClose}
              className="p-1 rounded-full hover:bg-white/20 text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-5 flex-1 text-slate-800 dark:text-slate-200">
          {isLoading ? (
            <div className="py-16 text-center space-y-3">
              <Loader2 className="w-7 h-7 animate-spin text-teal-600 mx-auto" />
              <p className="text-xs font-bold">Synthesizing Clinical Consultation Brief...</p>
            </div>
          ) : data ? (
            <>
              {/* Section 1: Recent Reports */}
              <div className="space-y-2.5">
                <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-600 font-heading">
                  <FileText className="w-4 h-4 text-teal-600" />
                  <span>Recent Diagnostic Reports</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {data.recent_reports.length === 0 ? (
                    <p className="text-xs text-slate-400">No reports uploaded.</p>
                  ) : (
                    data.recent_reports.map((r) => (
                      <div
                        key={r.id}
                        className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-700/60"
                      >
                        <p className="text-xs font-bold text-slate-900 dark:text-white truncate">
                          {r.title}
                        </p>
                        <p className="text-[11px] text-slate-500 mt-0.5">{r.extracted_measurements_summary}</p>
                        <p className="text-[10px] text-slate-400 mt-1">Date: {r.date || 'Undated'}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Section 2: Current Medications */}
              <div className="space-y-2.5">
                <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-600 font-heading">
                  <Pill className="w-4 h-4 text-teal-600" />
                  <span>Active & Recent Medications</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {data.current_medications.length === 0 ? (
                    <p className="text-xs text-slate-400">No active prescription records.</p>
                  ) : (
                    data.current_medications.map((m) => (
                      <div
                        key={m.id}
                        className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-700/60"
                      >
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-bold text-slate-900 dark:text-white">
                            {m.medicine_name}
                          </p>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200/60">
                            {m.dosage}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-1">
                          Frequency: {m.frequency} • Timing: {m.timing}
                        </p>
                        <p className="text-[10px] text-slate-400 mt-1">Source: {m.source_document_title}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Section 3: Biomarker Trajectories */}
              <div className="space-y-2.5">
                <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-600 font-heading">
                  <Activity className="w-4 h-4 text-teal-600" />
                  <span>Biomarker Trajectories</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {data.health_trends.length === 0 ? (
                    <p className="text-xs text-slate-400">No multi-report trajectories available.</p>
                  ) : (
                    data.health_trends.map((t, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/70 dark:border-slate-700/60"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-slate-900 dark:text-white truncate">
                            {t.test_name}
                          </span>
                          <span className="text-xs font-bold text-teal-700">
                            {t.current_value} {t.unit || ''}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-1">
                          History: {t.trend_summary}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Section 4: Questions to Discuss */}
              <div className="space-y-2.5">
                <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-600 font-heading">
                  <HelpCircle className="w-4 h-4 text-teal-600" />
                  <span>Discussion Topics Prepared for Physician</span>
                </div>
                <div className="space-y-2">
                  {data.questions_to_discuss.map((q, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-teal-50/40 dark:bg-teal-950/20 border border-teal-200/60 text-xs font-medium"
                    >
                      • {q.question_text || q}
                    </div>
                  ))}
                </div>
              </div>

              {/* Disclaimer */}
              <div className="p-3.5 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-[11px] text-slate-500">
                <strong>Doctor Visit Notice:</strong> This summary is an aggregation of personal records stored in HealthMate AI. It is intended to assist discussions with a licensed clinician.
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
};

export default DoctorVisitModal;
