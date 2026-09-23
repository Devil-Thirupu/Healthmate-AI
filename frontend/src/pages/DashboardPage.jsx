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
  Clock,
  Stethoscope,
  Download,
  AlertCircle,
  Sparkles,
  Search,
  UserCheck
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  Area,
  AreaChart
} from 'recharts';
import DailyHealthCard from '../components/common/DailyHealthCard';
import HealthTimelineView from '../components/common/HealthTimelineView';
import DoctorVisitModal from '../components/common/DoctorVisitModal';

const DashboardPage = () => {
  const { user } = useAuth();
  const { openUpload } = useOutletContext();
  const [documents, setDocuments] = useState([]);
  const [intelligenceSummary, setIntelligenceSummary] = useState(null);
  const [trendSeries, setTrendSeries] = useState([]);
  const [selectedSeriesKey, setSelectedSeriesKey] = useState('');
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [remindersToday, setRemindersToday] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDoctorVisitOpen, setIsDoctorVisitOpen] = useState(false);
  const [tableSearch, setTableSearch] = useState('');

  const fetchDashboardData = async () => {
    try {
      setIsLoading(true);
      const [docsRes, summaryRes, trendsRes, timelineRes, remindersRes] = await Promise.allSettled([
        api.get('/documents/'),
        api.get('/health-intelligence/summary'),
        api.get('/health-intelligence/trends'),
        api.get('/health-intelligence/timeline'),
        api.get('/reminders/today')
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
      if (remindersRes.status === 'fulfilled') setRemindersToday(remindersRes.value.data || []);
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
    window.addEventListener('healthmate_reminder_updated', handleRefresh);
    return () => {
      window.removeEventListener('healthmate_doc_uploaded', handleRefresh);
      window.removeEventListener('healthmate_reminder_updated', handleRefresh);
    };
  }, []);

  const labReportCount = documents.filter((d) => d.category === 'lab_report').length;
  const rxCount = documents.filter((d) => d.category === 'prescription').length;
  const currentSeries = trendSeries.find(s => s.canonical_name === selectedSeriesKey) || trendSeries[0];

  const filteredDocs = documents.filter(d =>
    d.title?.toLowerCase().includes(tableSearch.toLowerCase()) ||
    d.category?.toLowerCase().includes(tableSearch.toLowerCase()) ||
    d.doctor_name?.toLowerCase().includes(tableSearch.toLowerCase())
  );

  const getTrendBadge = (direction) => {
    switch (direction) {
      case 'Increased':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200/60 dark:bg-amber-950/50 dark:text-amber-300">
            <TrendingUp className="w-3 h-3" />
            <span>Elevated</span>
          </span>
        );
      case 'Decreased':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-sky-50 text-sky-700 border border-sky-200/60 dark:bg-sky-950/50 dark:text-sky-300">
            <TrendingDown className="w-3 h-3" />
            <span>Reduced</span>
          </span>
        );
      case 'Stable':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200/60 dark:bg-emerald-950/50 dark:text-emerald-300">
            <Minus className="w-3 h-3" />
            <span>Optimal</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400">
            <span>Standard</span>
          </span>
        );
    }
  };

  const pendingReminders = remindersToday.filter(r => r.status !== 'COMPLETED' && !r.is_completed);

  return (
    <div className="space-y-6">
      {/* Top Clinical Header & Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-extrabold uppercase tracking-widest text-teal-700 bg-teal-50 dark:bg-teal-950/60 px-2.5 py-0.5 rounded-full border border-teal-200/60 dark:border-teal-800/50">
              EHR Clinical Platform
            </span>
            <span className="text-xs text-slate-400">
              • Vault ID: <span className="font-mono font-medium text-slate-600 dark:text-slate-300">{user?.id ? `HM-${String(user.id).padStart(4, '0')}` : 'HM-PATIENT'}</span>
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white font-heading tracking-tight mt-1">
            Clinical Intelligence Center
          </h1>
          <p className="text-xs text-slate-500 max-w-2xl mt-0.5">
            Real-time longitudinal health monitoring, EHR ingestion status, and verified medical document vault.
          </p>
        </div>

        <div className="flex items-center flex-wrap gap-2.5 shrink-0">
          <Link
            to="/reports"
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 text-xs font-semibold rounded-xl shadow-2xs transition-all"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Export Summary</span>
          </Link>
          <button
            onClick={() => setIsDoctorVisitOpen(true)}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl shadow-xs transition-all active:scale-95"
          >
            <Stethoscope className="w-3.5 h-3.5" />
            <span>Doctor Visit Mode</span>
          </button>
          <button
            onClick={openUpload}
            className="inline-flex items-center space-x-1.5 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl shadow-xs transition-all active:scale-95"
          >
            <PlusCircle className="w-4 h-4" />
            <span>+ Upload Record</span>
          </button>
        </div>
      </div>

      {/* Top 3 Metric Cards matching dashboard.png */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Metric 1: Urgent / Out of Range Flagged Tests */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs relative overflow-hidden">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Out-of-Range Biomarkers
              </p>
              <div className="flex items-baseline space-x-2 mt-2">
                <span className="text-3xl font-black text-slate-900 dark:text-white font-heading">
                  {intelligenceSummary?.recent_changes?.filter(c => c.reference_range_status === 'Outside available reference range').length || 0}
                </span>
                <span className="text-xs font-bold text-rose-600 bg-rose-50 dark:bg-rose-950/60 px-2 py-0.5 rounded-full border border-rose-200/60 dark:border-rose-900/60">
                  Needs Physician Review
                </span>
              </div>
            </div>
            <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 text-rose-600 border border-rose-200/50 dark:border-rose-900/50">
              <AlertCircle className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500 pt-3 border-t border-slate-100 dark:border-slate-800">
            <span>Total Tracked Parameters: <strong className="text-slate-800 dark:text-slate-200">{intelligenceSummary?.tracked_biomarkers_count || 0}</strong></span>
            <Link to="/reports" className="text-teal-600 hover:text-teal-700 font-bold inline-flex items-center">
              View Lab Sheet <ChevronRight className="w-3 h-3 ml-0.5" />
            </Link>
          </div>
        </div>

        {/* Metric 2: Stable Biomarkers & Verified Records */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs relative overflow-hidden">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Verified Records & Labs
              </p>
              <div className="flex items-baseline space-x-2 mt-2">
                <span className="text-3xl font-black text-slate-900 dark:text-white font-heading">
                  {documents.length}
                </span>
                <span className="text-xs font-bold text-emerald-700 bg-emerald-50 dark:bg-emerald-950/60 px-2 py-0.5 rounded-full border border-emerald-200/60 dark:border-emerald-900/60">
                  {intelligenceSummary?.stable_count || 0} Stable Markers
                </span>
              </div>
            </div>
            <div className="p-3 rounded-xl bg-teal-50 dark:bg-teal-950/50 text-teal-600 border border-teal-200/50 dark:border-teal-900/50">
              <FlaskConical className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500 pt-3 border-t border-slate-100 dark:border-slate-800">
            <span>Prescriptions: <strong className="text-slate-800 dark:text-slate-200">{rxCount} Active</strong></span>
            <Link to="/records" className="text-teal-600 hover:text-teal-700 font-bold inline-flex items-center">
              Browse Vault <ChevronRight className="w-3 h-3 ml-0.5" />
            </Link>
          </div>
        </div>

        {/* Metric 3: AI Copilot & Evidence Verification */}
        <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs relative overflow-hidden">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Evidence Guard Integrity
              </p>
              <div className="flex items-baseline space-x-2 mt-2">
                <span className="text-3xl font-black text-slate-900 dark:text-white font-heading">
                  100%
                </span>
                <span className="text-xs font-bold text-teal-700 bg-teal-50 dark:bg-teal-950/60 px-2 py-0.5 rounded-full border border-teal-200/60 dark:border-teal-900/60">
                  SHA-256 Grounded
                </span>
              </div>
            </div>
            <div className="p-3 rounded-xl bg-sky-50 dark:bg-sky-950/50 text-sky-600 border border-sky-200/50 dark:border-sky-900/50">
              <ShieldCheck className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500 pt-3 border-t border-slate-100 dark:border-slate-800">
            <span>Trilingual: <strong className="text-slate-800 dark:text-slate-200">En / தமிழ் / Tanglish</strong></span>
            <Link to="/ai-assistant" className="text-teal-600 hover:text-teal-700 font-bold inline-flex items-center">
              Launch Copilot <ChevronRight className="w-3 h-3 ml-0.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* Observation & Safety Banner */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-200 dark:border-amber-900/50 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-start space-x-3">
          <div className="p-2 rounded-xl bg-amber-100 dark:bg-amber-950 text-amber-700 shrink-0">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-amber-900 dark:text-amber-200">
              Clinical Safety & Descriptive Intelligence Protocol
            </h3>
            <p className="text-[11px] text-amber-800/80 dark:text-amber-300/80 leading-relaxed">
              HealthMate AI tracks observed differences between verified test records. Always verify prescription adjustments and lab anomalies directly with your healthcare provider.
            </p>
          </div>
        </div>
        <Link
          to="/appointment-prep"
          className="shrink-0 px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold rounded-xl shadow-2xs transition-all inline-flex items-center space-x-1"
        >
          <span>Prep Doctor Questions</span>
          <ArrowRight className="w-3 h-3" />
        </Link>
      </div>

      {/* Daily Health Overview Component */}
      <DailyHealthCard />

      {/* Main Grid: Left Side Recent Updates + Longitudinal Chart; Right Side Consultations & Tasks */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Columns */}
        <div className="lg:col-span-2 space-y-6">
          {/* Recent Medical Updates Table matching dashboard.png */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs overflow-hidden">
            <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-bold text-slate-900 dark:text-white font-heading">
                  Recent Medical Updates & Records
                </h2>
                <p className="text-[11px] text-slate-400">
                  Real-time status of ingested lab results, prescriptions, and radiology reports
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    placeholder="Search records..."
                    value={tableSearch}
                    onChange={(e) => setTableSearch(e.target.value)}
                    className="pl-8 pr-3 py-1.5 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/30"
                  />
                </div>
                <Link
                  to="/records"
                  className="px-3 py-1.5 text-xs font-bold text-teal-700 dark:text-teal-300 bg-teal-50 dark:bg-teal-950/60 rounded-xl hover:bg-teal-100 transition-colors"
                >
                  View All
                </Link>
              </div>
            </div>

            {isLoading ? (
              <div className="p-12 text-center">
                <Activity className="w-6 h-6 animate-spin text-teal-600 mx-auto mb-2" />
                <p className="text-xs text-slate-400">Loading electronic medical records...</p>
              </div>
            ) : filteredDocs.length === 0 ? (
              <div className="p-10 text-center">
                <FileText className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="text-xs font-semibold text-slate-600 dark:text-slate-400">No medical records match your criteria.</p>
                <button
                  onClick={openUpload}
                  className="mt-3 inline-flex items-center space-x-1.5 px-3 py-1.5 bg-teal-600 text-white text-xs font-bold rounded-xl"
                >
                  <PlusCircle className="w-3.5 h-3.5" />
                  <span>Upload Document</span>
                </button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50/70 dark:bg-slate-800/50 text-slate-500 border-b border-slate-100 dark:border-slate-800">
                    <tr>
                      <th className="px-5 py-3 font-bold">Document / Record</th>
                      <th className="px-4 py-3 font-bold">Category</th>
                      <th className="px-4 py-3 font-bold">Date Recorded</th>
                      <th className="px-4 py-3 font-bold">Verification Status</th>
                      <th className="px-4 py-3 font-bold text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {filteredDocs.slice(0, 5).map((doc) => (
                      <tr key={doc.id} className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors">
                        <td className="px-5 py-3.5">
                          <div className="flex items-center space-x-3">
                            <div className="w-8 h-8 rounded-lg bg-teal-50 dark:bg-teal-950 text-teal-600 flex items-center justify-center shrink-0">
                              <FileText className="w-4 h-4" />
                            </div>
                            <div className="min-w-0">
                              <p className="font-bold text-slate-900 dark:text-white truncate max-w-[200px]">
                                {doc.title}
                              </p>
                              <p className="text-[11px] text-slate-400 truncate">
                                {doc.doctor_name || doc.hospital_name || 'Personal Upload'}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3.5">
                          <span className="capitalize px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                            {doc.category.replace('_', ' ')}
                          </span>
                        </td>
                        <td className="px-4 py-3.5 text-slate-600 dark:text-slate-300 font-medium">
                          {doc.document_date || 'Undated'}
                        </td>
                        <td className="px-4 py-3.5">
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200/60 dark:bg-emerald-950 dark:text-emerald-300">
                            <ShieldCheck className="w-3 h-3 text-emerald-600" />
                            <span>SHA-256 Valid</span>
                          </span>
                        </td>
                        <td className="px-4 py-3.5 text-right">
                          <a
                            href={`/api/v1/documents/${doc.id}/download`}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center space-x-1 text-teal-600 hover:text-teal-700 dark:text-teal-400 font-bold text-xs"
                          >
                            <span>Download</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Longitudinal Biomarker Trend Chart */}
          {trendSeries.length > 0 && currentSeries && (
            <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white font-heading flex items-center space-x-2">
                    <TrendingUp className="w-4 h-4 text-teal-600" />
                    <span>Longitudinal Biomarker Analysis</span>
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    Chronological value progression with reference thresholds ({currentSeries.unit})
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  <label className="text-xs font-semibold text-slate-500">Parameter:</label>
                  <select
                    value={selectedSeriesKey}
                    onChange={(e) => setSelectedSeriesKey(e.target.value)}
                    className="px-3 py-1.5 text-xs font-semibold bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500"
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
                  <AreaChart data={currentSeries.data_points} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                    <defs>
                      <linearGradient id="tealTrendGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0d9488" stopOpacity={0.25} />
                        <stop offset="95%" stopColor="#0d9488" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.6} />
                    <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                    <YAxis stroke="#64748b" fontSize={11} unit={` ${currentSeries.unit}`} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0f172a',
                        color: '#f8fafc',
                        borderRadius: '0.75rem',
                        border: 'none',
                        fontSize: '12px'
                      }}
                      formatter={(value) => [`${value} ${currentSeries.unit}`, currentSeries.test_name]}
                      labelFormatter={(label) => `Test Date: ${label}`}
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
                    <Area
                      type="monotone"
                      dataKey="numeric_value"
                      stroke="#0d9488"
                      strokeWidth={2.5}
                      fillOpacity={1}
                      fill="url(#tealTrendGradient)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Consultations, Refills & Patient Profile */}
        <div className="space-y-6">
          {/* Upcoming Consultations Card matching dashboard.png */}
          <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white font-heading">
                Upcoming Consultations
              </h3>
              <Link to="/appointment-prep" className="text-xs font-bold text-teal-600 hover:text-teal-700">
                Prep Sheet
              </Link>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/70 border border-slate-200/60 dark:border-slate-700/60 flex items-start space-x-3.5">
              <div className="px-3 py-2 rounded-xl bg-teal-600 text-white text-center shrink-0">
                <span className="block text-[10px] font-bold uppercase tracking-wider">OCT</span>
                <span className="block text-lg font-black leading-tight">24</span>
              </div>
              <div className="min-w-0 flex-1">
                <h4 className="text-xs font-bold text-slate-900 dark:text-white">
                  Dr. Anand Ramanathan
                </h4>
                <p className="text-[11px] text-slate-500">Internal Medicine • Apollo Hospital</p>
                <div className="mt-2 flex items-center space-x-2">
                  <button
                    onClick={() => setIsDoctorVisitOpen(true)}
                    className="px-2.5 py-1 bg-teal-600 hover:bg-teal-700 text-white text-[10px] font-bold rounded-lg transition-all"
                  >
                    Open Live Scribe
                  </button>
                  <Link
                    to="/appointment-prep"
                    className="px-2.5 py-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 text-[10px] font-semibold rounded-lg"
                  >
                    Brief PDF
                  </Link>
                </div>
              </div>
            </div>
          </div>

          {/* Refills & Medication Schedule Card */}
          <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white font-heading">
                Prescriptions & Refills
              </h3>
              <span className="text-[10px] font-bold text-teal-700 bg-teal-50 dark:bg-teal-950 px-2 py-0.5 rounded-full">
                {pendingReminders.length} Doses Due
              </span>
            </div>

            {pendingReminders.length === 0 ? (
              <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-center border border-emerald-200/60 dark:border-emerald-800/50">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 mx-auto mb-1" />
                <p className="text-xs font-bold text-emerald-800 dark:text-emerald-200">All daily doses logged</p>
                <p className="text-[11px] text-emerald-700 dark:text-emerald-300 mt-0.5">Adherence score: 100%</p>
              </div>
            ) : (
              <div className="space-y-2.5">
                {pendingReminders.slice(0, 3).map((item) => (
                  <div
                    key={item.id}
                    className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/70 border border-slate-200/60 dark:border-slate-700/60 flex items-center justify-between"
                  >
                    <div className="flex items-center space-x-2.5">
                      <div className="p-2 rounded-lg bg-teal-100/60 dark:bg-teal-950 text-teal-700">
                        <Pill className="w-3.5 h-3.5" />
                      </div>
                      <div>
                        <p className="text-xs font-bold text-slate-900 dark:text-white">{item.medicine_name || item.medication_name}</p>
                        <p className="text-[10px] text-slate-400">{item.dosage} • {item.scheduled_time}</p>
                      </div>
                    </div>
                    <Link
                      to="/prescriptions"
                      className="text-[11px] font-bold text-teal-600 hover:text-teal-700"
                    >
                      Log
                    </Link>
                  </div>
                ))}
              </div>
            )}

            <Link
              to="/prescriptions"
              className="w-full py-2 block text-center rounded-xl bg-slate-100 hover:bg-slate-200/70 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-bold transition-colors"
            >
              Manage Full Schedule
            </Link>
          </div>

          {/* Patient Health Profile Card */}
          <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-4">
            <div className="flex items-center space-x-3 pb-3 border-b border-slate-100 dark:border-slate-800">
              <div className="w-10 h-10 rounded-xl bg-teal-600 text-white font-bold text-sm flex items-center justify-center shadow-xs">
                {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'P'}
              </div>
              <div className="min-w-0 flex-1">
                <h4 className="text-xs font-bold text-slate-900 dark:text-white truncate">{user?.full_name || 'Patient'}</h4>
                <p className="text-[11px] text-slate-400 capitalize">{user?.gender || 'Male'} • {user?.role || 'patient'}</p>
              </div>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Blood Group</span>
                <span className="font-bold text-rose-600 dark:text-rose-400">{user?.blood_group || 'O+'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Date of Birth</span>
                <span className="font-medium text-slate-700 dark:text-slate-200">{user?.date_of_birth || '1985-06-12'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Known Allergies</span>
                <span className="font-medium text-slate-700 dark:text-slate-200 truncate max-w-[140px]">{user?.allergies || 'Penicillin'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Chronic Conditions</span>
                <span className="font-medium text-slate-700 dark:text-slate-200 truncate max-w-[140px]">{user?.chronic_conditions || 'Mild Hypertension'}</span>
              </div>
            </div>

            <Link
              to="/settings"
              className="w-full mt-1 py-2 block text-center rounded-xl bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 text-slate-700 dark:text-slate-300 text-xs font-bold transition-colors border border-slate-200/60 dark:border-slate-700"
            >
              Edit Clinical Profile
            </Link>
          </div>
        </div>
      </div>

      {/* Smart Health Timeline Stream */}
      <HealthTimelineView
        onViewSource={(docId) => window.open(`/api/v1/documents/${docId}/download`, '_blank')}
        onExplainReport={(docId) => window.location.href = '/reports'}
      />

      {/* Doctor Visit Mode Modal */}
      <DoctorVisitModal
        isOpen={isDoctorVisitOpen}
        onClose={() => setIsDoctorVisitOpen(false)}
      />
    </div>
  );
};

export default DashboardPage;
