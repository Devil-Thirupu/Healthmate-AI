import React, { useState, useEffect } from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import {
  Activity,
  FolderOpen,
  FlaskConical,
  Pill,
  BotMessageSquare,
  ShieldCheck,
  PlusCircle,
  AlertTriangle,
  FileText,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Minus,
  Heart,
  Share2,
  Calendar,
  Layers,
  CheckCircle2,
  ExternalLink,
  ChevronRight,
  Clock
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine
} from 'recharts';

const DashboardPage = () => {
  const { user } = useAuth();
  const { openUpload } = useOutletContext();
  const [documents, setDocuments] = useState([]);
  const [intelligenceSummary, setIntelligenceSummary] = useState(null);
  const [trendSeries, setTrendSeries] = useState([]);
  const [selectedSeriesKey, setSelectedSeriesKey] = useState('');
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      setIsLoading(true);
      const [docsRes, summaryRes, trendsRes, timelineRes] = await Promise.allSettled([
        api.get('/documents/'),
        api.get('/health-intelligence/summary'),
        api.get('/health-intelligence/trends'),
        api.get('/health-intelligence/timeline')
      ]);

      if (docsRes.status === 'fulfilled') setDocuments(docsRes.value.data || []);
      if (summaryRes.status === 'fulfilled') setIntelligenceSummary(summaryRes.value.data);
      if (trendsRes.status === 'fulfilled') {
        const trends = trendsRes.value.data || [];
        setTrendSeries(trends);
        if (trends.length > 0) {
          setSelectedSeriesKey(trends[0].canonical_name);
        }
      }
      if (timelineRes.status === 'fulfilled') setTimelineEvents(timelineRes.value.data || []);
    } catch (err) {
      console.error('Failed to load dashboard records:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const handleRefresh = () => fetchDashboardData();
    window.addEventListener('healthmate_doc_uploaded', handleRefresh);
    return () => window.removeEventListener('healthmate_doc_uploaded', handleRefresh);
  }, []);

  const labReportCount = documents.filter((d) => d.category === 'lab_report').length;
  const rxCount = documents.filter((d) => d.category === 'prescription').length;
  const imagingCount = documents.filter((d) => d.category === 'imaging').length;

  const currentSeries = trendSeries.find(s => s.canonical_name === selectedSeriesKey) || trendSeries[0];

  const getTrendBadge = (direction) => {
    switch (direction) {
      case 'Increased':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">
            <TrendingUp className="w-3 h-3" />
            <span>Increased</span>
          </span>
        );
      case 'Decreased':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">
            <TrendingDown className="w-3 h-3" />
            <span>Decreased</span>
          </span>
        );
      case 'Stable':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
            <Minus className="w-3 h-3" />
            <span>Stable</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400">
            <span>Insufficient data</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-brand-600 via-cyan-600 to-teal-600 text-white shadow-xl shadow-brand-500/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-white/20 text-white backdrop-blur">
              Personal Health Vault
            </span>
            <span className="text-xs text-brand-100">
              Language: {user?.language_preference === 'ta' ? 'தமிழ்' : user?.language_preference === 'tanglish' ? 'Tanglish' : 'English'}
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold font-heading tracking-tight">
            Welcome back, {user?.full_name || 'Patient'}
          </h1>
          <p className="text-xs text-brand-100 max-w-xl">
            Your personal medical records are securely stored, SHA-256 verified, and analyzed with descriptive health intelligence.
          </p>
        </div>

        <div className="flex items-center space-x-2.5 shrink-0">
          <button
            onClick={openUpload}
            className="inline-flex items-center space-x-2 px-4 py-2.5 bg-white text-brand-700 hover:bg-brand-50 text-xs font-bold rounded-xl shadow-md transition-all active:scale-95"
          >
            <PlusCircle className="w-4 h-4 text-brand-600" />
            <span>Upload Document</span>
          </button>
          <Link
            to="/ai-assistant"
            className="inline-flex items-center space-x-2 px-4 py-2.5 bg-black/20 hover:bg-black/30 text-white text-xs font-bold rounded-xl backdrop-blur transition-all"
          >
            <BotMessageSquare className="w-4 h-4 text-cyan-200" />
            <span>Ask AI Assistant</span>
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Total Documents</span>
            <div className="w-8 h-8 rounded-lg bg-brand-50 dark:bg-brand-950 text-brand-600 dark:text-brand-400 flex items-center justify-center">
              <FolderOpen className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-white mt-2 font-heading">
            {documents.length}
          </p>
          <p className="text-[11px] text-emerald-600 dark:text-emerald-400 mt-1 flex items-center space-x-1">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>100% SHA-256 Verified</span>
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Tracked Biomarkers</span>
            <div className="w-8 h-8 rounded-lg bg-cyan-50 dark:bg-cyan-950 text-cyan-600 dark:text-cyan-400 flex items-center justify-center">
              <FlaskConical className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-white mt-2 font-heading">
            {intelligenceSummary?.tracked_biomarkers_count || 0}
          </p>
          <Link to="/reports" className="text-[11px] text-brand-600 dark:text-brand-400 mt-1 inline-flex items-center space-x-1">
            <span>Compare Reports</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Prescriptions</span>
            <div className="w-8 h-8 rounded-lg bg-teal-50 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center">
              <Pill className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-white mt-2 font-heading">
            {rxCount}
          </p>
          <Link to="/prescriptions" className="text-[11px] text-teal-600 dark:text-teal-400 mt-1 inline-flex items-center space-x-1">
            <span>View Medications</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Stable Parameters</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-900 dark:text-white mt-2 font-heading">
            {intelligenceSummary?.stable_count || 0}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Relative diff ≤ 1.0%</p>
        </div>
      </div>

      {/* Health Observation & Safety Protocol Banner */}
      <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 flex items-start space-x-3">
        <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <h3 className="text-xs font-bold text-amber-800 dark:text-amber-300">
            Health Intelligence Observation & Safety Protocol
          </h3>
          <p className="text-xs text-amber-700 dark:text-amber-400/90 leading-relaxed">
            The Health Intelligence Engine reports observed changes between your verified medical records only. It does NOT provide clinical diagnoses, predictions, or prescription alterations. Always consult your physician.
          </p>
        </div>
      </div>

      {/* ----------------------------------------------------------------------------- */}
      {/* HEALTH INTELLIGENCE: RECENT BIOMARKER CHANGES & LONGITUDINAL TREND CHART */}
      {/* ----------------------------------------------------------------------------- */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white font-heading flex items-center space-x-2">
              <Activity className="w-4 h-4 text-brand-600" />
              <span>Health Intelligence: Biomarker Changes</span>
            </h2>
            <p className="text-xs text-slate-500">
              Descriptive analysis comparing previous vs latest measurements with source traceability
            </p>
          </div>

          <Link
            to="/reports"
            className="text-xs font-semibold text-brand-600 dark:text-brand-400 hover:underline inline-flex items-center space-x-1"
          >
            <span>Advanced Multi-Report Comparison</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Recent Changes Table */}
        {(!intelligenceSummary || intelligenceSummary.recent_changes.length === 0) ? (
          <div className="p-8 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
            <FlaskConical className="w-8 h-8 text-slate-300 dark:text-slate-600 mx-auto mb-2" />
            <p className="text-xs font-medium text-slate-600 dark:text-slate-400">
              No historical lab tests available for trend intelligence.
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Upload 2 or more lab reports to generate automated previous vs latest biomarker changes.
            </p>
          </div>
        ) : (
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Test Parameter</th>
                    <th className="px-4 py-3 font-semibold">Previous Value</th>
                    <th className="px-4 py-3 font-semibold">Latest Value</th>
                    <th className="px-4 py-3 font-semibold">Change</th>
                    <th className="px-4 py-3 font-semibold">% Change</th>
                    <th className="px-4 py-3 font-semibold">Trend</th>
                    <th className="px-4 py-3 font-semibold">Reference Status</th>
                    <th className="px-4 py-3 font-semibold text-right">Source Document</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {intelligenceSummary.recent_changes.map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="px-4 py-3 font-bold text-slate-900 dark:text-white">
                        {item.test_name}
                        <span className="block text-[10px] font-normal text-slate-400">{item.test_category}</span>
                      </td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                        {item.previous_value}
                        {item.previous_date !== 'Not available' && (
                          <span className="block text-[10px] text-slate-400">{item.previous_date}</span>
                        )}
                      </td>
                      <td className="px-4 py-3 font-semibold text-slate-900 dark:text-white">
                        {item.latest_value}
                        {item.latest_date !== 'Not available' && (
                          <span className="block text-[10px] text-slate-400">{item.latest_date}</span>
                        )}
                      </td>
                      <td className="px-4 py-3 font-mono font-medium text-slate-800 dark:text-slate-200">
                        {item.change}
                      </td>
                      <td className="px-4 py-3 font-mono font-bold">
                        <span
                          className={
                            item.percentage_change.startsWith('+')
                              ? 'text-amber-600 dark:text-amber-400'
                              : item.percentage_change.startsWith('-')
                              ? 'text-blue-600 dark:text-blue-400'
                              : 'text-slate-600 dark:text-slate-400'
                          }
                        >
                          {item.percentage_change}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        {getTrendBadge(item.trend_direction)}
                      </td>
                      <td className="px-4 py-3">
                        {item.reference_range_status === 'Within available reference range' ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
                            Within range
                          </span>
                        ) : item.reference_range_status === 'Outside available reference range' ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300">
                            Outside range
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-normal text-slate-400">
                            Not available
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {item.source_document_id ? (
                          <a
                            href={`/api/v1/documents/${item.source_document_id}/download`}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold text-brand-600 dark:text-brand-400 hover:bg-brand-50 dark:hover:bg-brand-950 border border-brand-200 dark:border-brand-800 transition-colors"
                          >
                            <span>View Source</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        ) : (
                          <span className="text-[11px] text-slate-400">Original Document</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ----------------------------------------------------------------------------- */}
        {/* BIOMARKER LONGITUDINAL TREND CHART (Recharts) */}
        {/* ----------------------------------------------------------------------------- */}
        {trendSeries.length > 0 && currentSeries && (
          <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white font-heading flex items-center space-x-2">
                  <TrendingUp className="w-4 h-4 text-cyan-600" />
                  <span>Biomarker Longitudinal Trend Chart</span>
                </h3>
                <p className="text-[11px] text-slate-400">
                  Chronological data points plotted with identical unit safety ({currentSeries.unit})
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <label className="text-xs font-semibold text-slate-500">Select Biomarker:</label>
                <select
                  value={selectedSeriesKey}
                  onChange={(e) => setSelectedSeriesKey(e.target.value)}
                  className="px-3 py-1.5 text-xs font-medium bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  {trendSeries.map((s, i) => (
                    <option key={i} value={s.canonical_name}>
                      {s.test_name} ({s.unit})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="h-64 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={currentSeries.data_points} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} unit={` ${currentSeries.unit}`} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      color: '#f8fafc',
                      borderRadius: '0.75rem',
                      border: 'none',
                      fontSize: '12px'
                    }}
                    formatter={(value) => [`${value} ${currentSeries.unit}`, currentSeries.test_name]}
                    labelFormatter={(label) => `Report Date: ${label}`}
                  />
                  {currentSeries.reference_range_max && (
                    <ReferenceLine
                      y={currentSeries.reference_range_max}
                      stroke="#ef4444"
                      strokeDasharray="4 4"
                      label={{ value: `Max: ${currentSeries.reference_range_max}`, fill: '#ef4444', fontSize: 10 }}
                    />
                  )}
                  {currentSeries.reference_range_min && (
                    <ReferenceLine
                      y={currentSeries.reference_range_min}
                      stroke="#10b981"
                      strokeDasharray="4 4"
                      label={{ value: `Min: ${currentSeries.reference_range_min}`, fill: '#10b981', fontSize: 10 }}
                    />
                  )}
                  <Line
                    type="monotone"
                    dataKey="numeric_value"
                    stroke="#0284c7"
                    strokeWidth={2.5}
                    dot={{ r: 4, fill: '#0284c7' }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      {/* ----------------------------------------------------------------------------- */}
      {/* CHRONOLOGICAL HEALTH RECORD TIMELINE */}
      {/* ----------------------------------------------------------------------------- */}
      {timelineEvents.length > 0 && (
        <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white font-heading flex items-center space-x-2">
                <Clock className="w-4 h-4 text-brand-600" />
                <span>Chronological Health Timeline</span>
              </h3>
              <p className="text-[11px] text-slate-400">
                Medical events and extracted diagnostic parameters ordered chronologically
              </p>
            </div>
          </div>

          <div className="relative border-l-2 border-slate-200 dark:border-slate-800 ml-4 space-y-6 py-2">
            {timelineEvents.slice(0, 5).map((evt, idx) => (
              <div key={idx} className="relative pl-6">
                <div className="absolute -left-[9px] top-1.5 w-4 h-4 rounded-full bg-brand-500 border-2 border-white dark:border-slate-900" />
                <div className="p-3.5 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200/80 dark:border-slate-800 space-y-2">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                    <h4 className="text-xs font-bold text-slate-900 dark:text-white">
                      {evt.document_title}
                    </h4>
                    <span className="text-[11px] font-mono text-slate-400 flex items-center space-x-1">
                      <Calendar className="w-3 h-3" />
                      <span>{evt.event_date}</span>
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-500">
                    Category: <span className="capitalize font-medium text-slate-700 dark:text-slate-300">{evt.document_category.replace('_', ' ')}</span>
                    {evt.clinic_or_lab && <span> • {evt.clinic_or_lab}</span>}
                    {evt.doctor_name && <span> • {evt.doctor_name}</span>}
                  </p>

                  {evt.measurements.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {evt.measurements.map((m, mIdx) => (
                        <span
                          key={mIdx}
                          className="px-2 py-0.5 rounded-lg text-[10px] font-medium bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300"
                        >
                          {m.test_name}: <strong className="text-slate-900 dark:text-white">{m.observed_value}</strong>
                        </span>
                      ))}
                    </div>
                  )}

                  {evt.prescriptions.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {evt.prescriptions.map((p, pIdx) => (
                        <span
                          key={pIdx}
                          className="px-2 py-0.5 rounded-lg text-[10px] font-medium bg-teal-50 dark:bg-teal-950/60 border border-teal-200 dark:border-teal-900 text-teal-800 dark:text-teal-300"
                        >
                          Rx: {p.medication_name} ({p.dosage || 'Standard'})
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Content Grid: Recent Documents & Patient Demographics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Recent Documents */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-900 dark:text-white font-heading">
              Recent Medical Records
            </h2>
            <Link
              to="/records"
              className="text-xs font-semibold text-brand-600 dark:text-brand-400 hover:underline inline-flex items-center space-x-1"
            >
              <span>View all ({documents.length})</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {isLoading ? (
            <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
              <Activity className="w-6 h-6 animate-spin text-brand-600 mx-auto mb-2" />
              <p className="text-xs text-slate-500">Loading your medical records...</p>
            </div>
          ) : documents.length === 0 ? (
            <div className="p-10 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 space-y-3">
              <FileText className="w-10 h-10 text-slate-300 dark:text-slate-600 mx-auto" />
              <div>
                <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">No medical records uploaded yet</h4>
                <p className="text-xs text-slate-400 mt-1">
                  Upload your first lab report or prescription to activate automated OCR and clinical intelligence.
                </p>
              </div>
              <button
                onClick={openUpload}
                className="inline-flex items-center space-x-1.5 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold rounded-xl shadow-sm transition-all"
              >
                <PlusCircle className="w-4 h-4" />
                <span>Upload First Document</span>
              </button>
            </div>
          ) : (
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 divide-y divide-slate-100 dark:divide-slate-800 overflow-hidden shadow-sm">
              {documents.slice(0, 5).map((doc) => (
                <div
                  key={doc.id}
                  className="p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors flex items-center justify-between gap-3"
                >
                  <div className="flex items-center space-x-3 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-brand-50 dark:bg-brand-950 text-brand-600 dark:text-brand-400 flex items-center justify-center shrink-0">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div className="min-w-0">
                      <h4 className="text-xs font-bold text-slate-900 dark:text-white truncate">
                        {doc.title}
                      </h4>
                      <p className="text-[11px] text-slate-400 flex items-center space-x-2 mt-0.5">
                        <span className="capitalize">{doc.category.replace('_', ' ')}</span>
                        <span>•</span>
                        <span>{doc.document_date || 'Undated'}</span>
                        {doc.doctor_name && (
                          <>
                            <span>•</span>
                            <span className="truncate">{doc.doctor_name}</span>
                          </>
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 shrink-0">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300">
                      SHA-256 OK
                    </span>
                    <Link
                      to="/records"
                      className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
                    >
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Col: Patient Health Profile */}
        <div className="space-y-4">
          <h2 className="text-base font-bold text-slate-900 dark:text-white font-heading">
            Patient Health Profile
          </h2>

          <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4 shadow-sm">
            <div className="flex items-center space-x-3 pb-3 border-b border-slate-100 dark:border-slate-800">
              <div className="w-11 h-11 rounded-full bg-gradient-to-br from-brand-500 to-teal-500 text-white font-bold text-sm flex items-center justify-center shadow-md">
                {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'P'}
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900 dark:text-white">{user?.full_name}</h4>
                <p className="text-[11px] text-slate-400 capitalize">{user?.gender || 'Not specified'} • {user?.role || 'patient'}</p>
              </div>
            </div>

            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Blood Group</span>
                <span className="font-bold text-rose-600 dark:text-rose-400">{user?.blood_group || 'Not recorded'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Date of Birth</span>
                <span className="font-medium text-slate-700 dark:text-slate-200">{user?.date_of_birth || 'Not recorded'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Known Allergies</span>
                <span className="font-medium text-slate-700 dark:text-slate-200 truncate max-w-[150px]">{user?.allergies || 'None recorded'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Chronic Conditions</span>
                <span className="font-medium text-slate-700 dark:text-slate-200 truncate max-w-[150px]">{user?.chronic_conditions || 'None recorded'}</span>
              </div>
            </div>

            <Link
              to="/settings"
              className="w-full mt-2 py-2 block text-center rounded-xl bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700/60 text-slate-700 dark:text-slate-300 text-xs font-semibold transition-colors"
            >
              Edit Health Profile
            </Link>
          </div>

          {/* Quick Clinical Shortcuts */}
          <div className="p-4 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-800 text-white space-y-3">
            <h4 className="text-xs font-bold text-cyan-400 uppercase tracking-wider font-heading">
              Clinical Quick Tools
            </h4>
            <div className="space-y-2">
              <Link
                to="/ai-assistant"
                className="w-full flex items-center justify-between p-2.5 rounded-xl bg-white/10 hover:bg-white/15 text-xs text-white transition-all"
              >
                <div className="flex items-center space-x-2">
                  <BotMessageSquare className="w-4 h-4 text-cyan-300" />
                  <span>Ask Medicine / Lab Queries</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-slate-300" />
              </Link>

              <Link
                to="/sharing"
                className="w-full flex items-center justify-between p-2.5 rounded-xl bg-white/10 hover:bg-white/15 text-xs text-white transition-all"
              >
                <div className="flex items-center space-x-2">
                  <Share2 className="w-4 h-4 text-emerald-300" />
                  <span>Generate Doctor Share PIN</span>
                </div>
                <ArrowRight className="w-3.5 h-3.5 text-slate-300" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
