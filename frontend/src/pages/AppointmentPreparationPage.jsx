import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  CalendarCheck,
  FileText,
  FlaskConical,
  Pill,
  Activity,
  TrendingUp,
  HelpCircle,
  ShieldCheck,
  Download,
  Edit3,
  Trash2,
  Plus,
  CheckCircle2,
  AlertTriangle,
  Eye,
  RefreshCw,
  Sliders,
  Check,
  X,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Stethoscope
} from 'lucide-react';
import DoctorVisitModal from '../components/common/DoctorVisitModal';

const AppointmentPreparationPage = () => {
  const { user } = useAuth();
  const [summaries, setSummaries] = useState([]);
  const [activeSummary, setActiveSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [isDoctorVisitOpen, setIsDoctorVisitOpen] = useState(false);
  
  // Customization state
  const [customTitle, setCustomTitle] = useState('');
  const [questions, setQuestions] = useState([]);
  const [newQuestionText, setNewQuestionText] = useState('');
  const [excludedSections, setExcludedSections] = useState([]);
  const [customNotes, setCustomNotes] = useState('');
  const [editingQuestionIdx, setEditingQuestionIdx] = useState(null);
  const [editQuestionValue, setEditQuestionValue] = useState('');
  const [saveSuccessMsg, setSaveSuccessMsg] = useState('');

  const fetchSummaries = async () => {
    try {
      setLoading(true);
      const res = await api.get('/appointment-summary/list');
      setSummaries(res.data || []);
      if (res.data && res.data.length > 0 && !activeSummary) {
        loadSummaryDetail(res.data[0].id);
      }
    } catch (err) {
      console.error('Failed to fetch summaries:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadSummaryDetail = async (summaryId) => {
    try {
      setLoading(true);
      const res = await api.get(`/appointment-summary/${summaryId}`);
      const sum = res.data;
      setActiveSummary(sum);
      setCustomTitle(sum.title || 'General Medical Consultation Summary');
      const data = sum.summary_data || {};
      setQuestions(data.generated_questions || []);
      setExcludedSections(data.excluded_sections || []);
      setCustomNotes(data.custom_notes || '');
    } catch (err) {
      console.error('Failed to load summary detail:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummaries();
  }, []);

  const handleGenerateNew = async () => {
    try {
      setGenerating(true);
      const res = await api.post('/appointment-summary/generate', {
        title: customTitle || 'General Medical Consultation Summary'
      });
      const newSum = res.data;
      setSummaries((prev) => [newSum, ...prev.filter((s) => s.id !== newSum.id)]);
      setActiveSummary(newSum);
      setCustomTitle(newSum.title);
      const data = newSum.summary_data || {};
      setQuestions(data.generated_questions || []);
      setExcludedSections(data.excluded_sections || []);
      setCustomNotes(data.custom_notes || '');
      setSaveSuccessMsg('New consultation preparation brief generated from vault records.');
      setTimeout(() => setSaveSuccessMsg(''), 4000);
    } catch (err) {
      console.error('Error generating summary:', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleSaveReview = async () => {
    if (!activeSummary) return;
    try {
      setSaving(true);
      const res = await api.put(`/appointment-summary/${activeSummary.id}`, {
        title: customTitle,
        generated_questions: questions,
        excluded_sections: excludedSections,
        custom_notes: customNotes
      });
      setActiveSummary(res.data);
      setSaveSuccessMsg('Appointment brief preferences saved.');
      setTimeout(() => setSaveSuccessMsg(''), 3000);
    } catch (err) {
      console.error('Failed to save summary review:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleDownloadPdf = async () => {
    if (!activeSummary) return;
    try {
      setDownloadingPdf(true);
      await api.put(`/appointment-summary/${activeSummary.id}`, {
        title: customTitle,
        generated_questions: questions,
        excluded_sections: excludedSections,
        custom_notes: customNotes
      });

      const res = await api.get(`/appointment-summary/${activeSummary.id}/pdf`, {
        responseType: 'blob'
      });

      const blob = new Blob([res.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `HealthMate_Consultation_Brief_${activeSummary.id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download PDF:', err);
    } finally {
      setDownloadingPdf(false);
    }
  };

  const toggleSection = (sectionKey) => {
    setExcludedSections((prev) =>
      prev.includes(sectionKey) ? prev.filter((k) => k !== sectionKey) : [...prev, sectionKey]
    );
  };

  const handleAddQuestion = () => {
    if (!newQuestionText.trim()) return;
    setQuestions((prev) => [...prev, newQuestionText.trim()]);
    setNewQuestionText('');
  };

  const handleDeleteQuestion = (idx) => {
    setQuestions((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleStartEditQuestion = (idx, text) => {
    setEditingQuestionIdx(idx);
    setEditQuestionValue(text);
  };

  const handleSaveEditQuestion = () => {
    if (editingQuestionIdx === null) return;
    setQuestions((prev) =>
      prev.map((q, i) => (i === editingQuestionIdx ? editQuestionValue.trim() || q : q))
    );
    setEditingQuestionIdx(null);
    setEditQuestionValue('');
  };

  const data = activeSummary?.summary_data || {};
  const recentDocs = data.recent_documents || [];
  const labTests = data.lab_measurements || [];
  const prescriptions = data.prescriptions || [];
  const sources = data.sources || [];

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-extrabold uppercase tracking-widest text-teal-700 bg-teal-50 dark:bg-teal-950/60 px-2.5 py-0.5 rounded-full border border-teal-200/60 dark:border-teal-800/50">
              Clinical Consultation Scribe
            </span>
            <span className="text-xs text-slate-400">
              • Physician Briefing Generator
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white font-heading tracking-tight mt-1">
            Appointment Preparation & Doctor Brief
          </h1>
          <p className="text-xs text-slate-500 max-w-2xl mt-0.5">
            Organize diagnostic records, generate evidence-backed clinical discussion questions, and export ReportLab briefing sheets.
          </p>
        </div>

        <div className="flex items-center flex-wrap gap-2.5 shrink-0">
          <button
            onClick={() => setIsDoctorVisitOpen(true)}
            className="px-3.5 py-2 rounded-xl text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 shadow-xs transition-all active:scale-95 inline-flex items-center space-x-1.5"
          >
            <Stethoscope className="w-3.5 h-3.5" />
            <span>Doctor Visit Mode</span>
          </button>

          <button
            onClick={handleGenerateNew}
            disabled={generating}
            className="px-3.5 py-2 rounded-xl text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 shadow-xs transition-all active:scale-95 disabled:opacity-50 inline-flex items-center space-x-1.5"
          >
            {generating ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Aggregating Vault...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>+ Generate New Brief</span>
              </>
            )}
          </button>

          {activeSummary && (
            <button
              onClick={handleDownloadPdf}
              disabled={downloadingPdf}
              className="px-3.5 py-2 rounded-xl text-xs font-bold text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 hover:bg-slate-50 border border-slate-200/90 dark:border-slate-700 shadow-2xs transition-all active:scale-95 disabled:opacity-50 inline-flex items-center space-x-1.5"
            >
              {downloadingPdf ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Exporting...</span>
                </>
              ) : (
                <>
                  <Download className="w-3.5 h-3.5" />
                  <span>Export PDF</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {saveSuccessMsg && (
        <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 text-xs font-bold text-emerald-800 dark:text-emerald-200 flex items-center space-x-2 animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>{saveSuccessMsg}</span>
        </div>
      )}

      {/* Main Split Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Sidebar: Saved Summaries & Section Toggles */}
        <div className="lg:col-span-1 space-y-4">
          <div className="p-4 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 font-heading flex items-center space-x-1.5">
              <CalendarCheck className="w-3.5 h-3.5 text-teal-600" />
              <span>Saved Summaries ({summaries.length})</span>
            </h2>

            {summaries.length === 0 ? (
              <p className="text-xs text-slate-400 italic py-2">
                Click "+ Generate New Brief" to create your first consultation sheet.
              </p>
            ) : (
              <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
                {summaries.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => loadSummaryDetail(s.id)}
                    className={`w-full text-left p-3 rounded-xl border text-xs transition-all ${
                      activeSummary?.id === s.id
                        ? 'bg-teal-50/70 dark:bg-teal-950/50 border-teal-500 ring-1 ring-teal-500 shadow-2xs'
                        : 'bg-slate-50/60 dark:bg-slate-800/60 border-slate-200/80 dark:border-slate-800 hover:border-teal-300'
                    }`}
                  >
                    <p className="font-bold text-slate-900 dark:text-white truncate">
                      {s.title}
                    </p>
                    <p className="text-[10px] text-slate-400 mt-1">
                      Created: {new Date(s.created_at).toLocaleDateString()}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Section Inclusion Toggles */}
          {activeSummary && (
            <div className="p-4 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-3">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 font-heading flex items-center space-x-1.5">
                <Sliders className="w-3.5 h-3.5 text-teal-600" />
                <span>PDF Section Toggles</span>
              </h2>
              <div className="space-y-1.5 text-xs">
                {[
                  { key: 'documents', label: 'Recent Documents', count: recentDocs.length },
                  { key: 'lab_measurements', label: 'Lab Measurements', count: labTests.length },
                  { key: 'prescriptions', label: 'Prescriptions', count: prescriptions.length },
                  { key: 'questions', label: 'Discussion Questions', count: questions.length },
                  { key: 'sources', label: 'Evidence Sources', count: sources.length },
                ].map((sec) => {
                  const isIncluded = !excludedSections.includes(sec.key);
                  return (
                    <button
                      key={sec.key}
                      onClick={() => toggleSection(sec.key)}
                      className={`w-full flex items-center justify-between px-3 py-2 rounded-xl font-bold transition-all ${
                        isIncluded
                          ? 'bg-teal-50 dark:bg-teal-950/40 text-teal-800 dark:text-teal-300 border border-teal-200/70'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-400 line-through'
                      }`}
                    >
                      <span>{sec.label}</span>
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-white/60 dark:bg-slate-900/60">
                        {sec.count}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Right Main Panel: Interactive Consultation Brief */}
        <div className="lg:col-span-3 space-y-4">
          {!activeSummary ? (
            <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 space-y-3">
              <CalendarCheck className="w-10 h-10 text-teal-600 mx-auto opacity-70" />
              <h3 className="text-sm font-bold text-slate-900 dark:text-white font-heading">
                No Consultation Brief Selected
              </h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                Generate an automated preparation summary from your verified reports to organize topics for your doctor.
              </p>
              <button
                onClick={handleGenerateNew}
                disabled={generating}
                className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 shadow-xs"
              >
                Generate Consultation Brief
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Brief Title Editor */}
              <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex-1">
                    <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                      Consultation Purpose / Clinical Title:
                    </label>
                    <input
                      type="text"
                      value={customTitle}
                      onChange={(e) => setCustomTitle(e.target.value)}
                      placeholder="e.g. Internal Medicine Follow-up, Annual Health Review"
                      className="w-full text-base font-bold text-slate-900 dark:text-white bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3.5 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500/30 font-heading"
                    />
                  </div>

                  <div className="flex items-center space-x-2 self-end sm:self-auto">
                    <button
                      onClick={handleSaveReview}
                      disabled={saving}
                      className="px-3.5 py-2 rounded-xl text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 shadow-xs transition-all active:scale-95 disabled:opacity-50 inline-flex items-center space-x-1"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>{saving ? 'Saving...' : 'Save Brief'}</span>
                    </button>
                  </div>
                </div>

                <div className="flex items-center gap-2 text-[11px] text-slate-400 pt-1 border-t border-slate-100 dark:border-slate-800">
                  <span>Patient: <strong className="text-slate-800 dark:text-slate-200">{data.patient_info?.full_name || user?.full_name}</strong></span>
                  <span>•</span>
                  <span>Generated Date: <strong>{data.generation_date}</strong></span>
                </div>
              </div>

              {/* Discussion Questions */}
              {!excludedSections.includes('questions') && (
                <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <HelpCircle className="w-4 h-4 text-teal-600" />
                      <h3 className="text-sm font-bold text-slate-900 dark:text-white font-heading">
                        Suggested Discussion Questions ({questions.length})
                      </h3>
                    </div>
                    <span className="text-[10px] text-slate-400">
                      Grounded in report abnormalities & trends
                    </span>
                  </div>

                  <div className="space-y-2">
                    {questions.map((q, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-teal-50/40 dark:bg-teal-950/20 border border-teal-200/60 dark:border-teal-900/40 rounded-xl text-xs flex items-start justify-between gap-3 group"
                      >
                        {editingQuestionIdx === idx ? (
                          <div className="flex-1 flex items-center space-x-2">
                            <input
                              type="text"
                              value={editQuestionValue}
                              onChange={(e) => setEditQuestionValue(e.target.value)}
                              className="flex-1 px-3 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-teal-300 text-xs text-slate-900 dark:text-white focus:outline-none"
                            />
                            <button
                              onClick={handleSaveEditQuestion}
                              className="p-1.5 bg-teal-600 text-white rounded-lg hover:bg-teal-700"
                            >
                              <Check className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => setEditingQuestionIdx(null)}
                              className="p-1.5 bg-slate-200 text-slate-600 rounded-lg"
                            >
                              <X className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        ) : (
                          <>
                            <div className="flex items-start space-x-2">
                              <span className="font-bold text-teal-700">
                                Q{idx + 1}.
                              </span>
                              <p className="text-slate-800 dark:text-slate-200 leading-relaxed font-medium">
                                {q}
                              </p>
                            </div>
                            <div className="flex items-center space-x-1 shrink-0 opacity-80 group-hover:opacity-100 transition-opacity">
                              <button
                                onClick={() => handleStartEditQuestion(idx, q)}
                                className="p-1 text-slate-400 hover:text-slate-600"
                                title="Edit Question"
                              >
                                <Edit3 className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={() => handleDeleteQuestion(idx)}
                                className="p-1 text-slate-400 hover:text-rose-600"
                                title="Remove Question"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </>
                        )}
                      </div>
                    ))}

                    <div className="flex items-center space-x-2 pt-2">
                      <input
                        type="text"
                        value={newQuestionText}
                        onChange={(e) => setNewQuestionText(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleAddQuestion()}
                        placeholder="Add a custom question to discuss with your physician..."
                        className="flex-1 px-3.5 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500/30"
                      />
                      <button
                        onClick={handleAddQuestion}
                        disabled={!newQuestionText.trim()}
                        className="px-3.5 py-2 rounded-xl text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 disabled:opacity-50 transition-colors inline-flex items-center space-x-1 shadow-2xs"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>Add</span>
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Health Measurements Table */}
              {!excludedSections.includes('lab_measurements') && (
                <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <FlaskConical className="w-4 h-4 text-teal-600" />
                      <h3 className="text-sm font-bold text-slate-900 dark:text-white font-heading">
                        Recent Lab Measurements ({labTests.length})
                      </h3>
                    </div>
                  </div>

                  {labTests.length === 0 ? (
                    <p className="text-xs text-slate-400 italic">No lab test records found in your vault.</p>
                  ) : (
                    <div className="overflow-x-auto rounded-xl border border-slate-200/90 dark:border-slate-800">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead className="bg-slate-50/80 dark:bg-slate-800 text-slate-500 font-bold border-b border-slate-100 dark:border-slate-800">
                          <tr>
                            <th className="py-2.5 px-3">Test Name</th>
                            <th className="py-2.5 px-3">Latest Value</th>
                            <th className="py-2.5 px-3">Previous</th>
                            <th className="py-2.5 px-3">Change</th>
                            <th className="py-2.5 px-3">Ref. Range</th>
                            <th className="py-2.5 px-3">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                          {labTests.map((t, idx) => (
                            <tr key={idx} className="hover:bg-slate-50/60 transition-colors">
                              <td className="py-2.5 px-3 font-bold text-slate-900 dark:text-white">
                                {t.test_name}
                              </td>
                              <td className="py-2.5 px-3 font-mono font-bold text-slate-800 dark:text-slate-200">
                                {t.latest_value} <span className="text-[10px] text-slate-400 font-normal">({t.date})</span>
                              </td>
                              <td className="py-2.5 px-3 text-slate-500 font-mono">
                                {t.previous_value}
                              </td>
                              <td className="py-2.5 px-3 font-mono font-bold text-teal-700">
                                {t.change} {t.percentage_change !== 'N/A' && `(${t.percentage_change})`}
                              </td>
                              <td className="py-2.5 px-3 text-slate-500">
                                {t.reference_range}
                              </td>
                              <td className="py-2.5 px-3">
                                <span
                                  className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                                    ['high', 'critical', 'abnormal', 'low'].includes(t.flag.toLowerCase())
                                      ? 'bg-rose-50 text-rose-700 border border-rose-200'
                                      : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                  }`}
                                >
                                  {t.flag}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* Active Prescriptions */}
              {!excludedSections.includes('prescriptions') && (
                <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-3">
                  <div className="flex items-center space-x-2">
                    <Pill className="w-4 h-4 text-teal-600" />
                    <h3 className="text-sm font-bold text-slate-900 dark:text-white font-heading">
                      Active Prescribed Medications ({prescriptions.length})
                    </h3>
                  </div>

                  {prescriptions.length === 0 ? (
                    <p className="text-xs text-slate-400 italic">No prescription records stored in your vault.</p>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {prescriptions.map((rx, idx) => (
                        <div key={idx} className="p-3.5 bg-slate-50/70 dark:bg-slate-800/60 rounded-xl border border-slate-200/80 dark:border-slate-700 text-xs space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-slate-900 dark:text-white">
                              {rx.medication_name}
                            </span>
                            <span className="px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 text-[10px] font-bold border border-teal-200/60">
                              {rx.dosage}
                            </span>
                          </div>
                          <p className="text-slate-600 dark:text-slate-300">
                            <strong>Frequency:</strong> {rx.frequency} — {rx.timing_instructions}
                          </p>
                          <p className="text-[10px] text-slate-400">
                            Dr: {rx.doctor_name} ({rx.prescribed_date})
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Doctor Visit Mode Modal */}
      <DoctorVisitModal
        isOpen={isDoctorVisitOpen}
        onClose={() => setIsDoctorVisitOpen(false)}
      />
    </div>
  );
};

export default AppointmentPreparationPage;
