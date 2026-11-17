import React, { useState, useEffect } from 'react';
import { Link, useOutletContext, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api, { getApiUrl } from '../services/api';
import {
  Upload, MessageSquare, TrendingUp, Utensils,
  Heart, Bell, ChevronRight, Download, ArrowRight,
  CheckCircle2, FileText, FlaskConical, Pill, Search
} from 'lucide-react';
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid
} from 'recharts';
import { getStoredDocuments } from '../services/documentStore';

const DashboardPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { openUpload } = useOutletContext();
  const [documents, setDocuments] = useState([]);
  const [remindersToday, setRemindersToday] = useState([]);
  const [trendSeries, setTrendSeries] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const firstName = user?.full_name ? user.full_name.split(' ')[0] : 'there';

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      try {
        const [docsRes, remRes, trendsRes] = await Promise.allSettled([
          api.get('/documents/'),
          api.get('/reminders/today'),
          api.get('/health-intelligence/trends'),
        ]);
        if (docsRes.status === 'fulfilled') setDocuments(docsRes.value.data || []);
        if (remRes.status === 'fulfilled') setRemindersToday(remRes.value.data || []);
        if (trendsRes.status === 'fulfilled') setTrendSeries(trendsRes.value.data || []);
      } catch (e) {}

      // Merge local docs
      const localDocs = getStoredDocuments();
      setDocuments(prev => {
        const merged = [...prev];
        for (const ld of localDocs) {
          if (!merged.some(d => d.id === ld.id)) merged.push(ld);
        }
        return merged;
      });
      setIsLoading(false);
    };
    load();
    window.addEventListener('healthmate_doc_uploaded', load);
    return () => window.removeEventListener('healthmate_doc_uploaded', load);
  }, []);

  const recentDocs = documents.slice(0, 3);
  const trendData = trendSeries[0]?.data_points || [
    { date: 'Aug', numeric_value: 110 },
    { date: 'Sep', numeric_value: 108 },
    { date: 'Oct', numeric_value: 105 },
    { date: 'Nov', numeric_value: 102 },
  ];

  const quickActions = [
    {
      icon: Upload,
      title: 'Upload Reports',
      desc: 'Scan or upload medical reports & prescriptions',
      color: 'bg-blue-50',
      iconColor: 'text-blue-500',
      onClick: openUpload,
    },
    {
      icon: MessageSquare,
      title: 'Ask AI Assistant',
      desc: 'Get instant answers about your health',
      color: 'bg-teal-50',
      iconColor: 'text-teal-500',
      onClick: () => navigate('/ai-assistant'),
    },
    {
      icon: TrendingUp,
      title: 'View Health Trends',
      desc: 'Track your health values over time',
      color: 'bg-purple-50',
      iconColor: 'text-purple-500',
      onClick: () => navigate('/reports'),
    },
    {
      icon: Utensils,
      title: 'Nutrition Tips',
      desc: 'Get personalized food suggestions',
      color: 'bg-orange-50',
      iconColor: 'text-orange-500',
      onClick: () => navigate('/nutrition'),
    },
  ];

  const getCategoryIcon = (category) => {
    if (category === 'prescription') return <Pill className="w-4 h-4 text-teal-600" />;
    if (category === 'lab_report') return <FlaskConical className="w-4 h-4 text-blue-600" />;
    return <FileText className="w-4 h-4 text-slate-500" />;
  };

  const getCategoryBg = (category) => {
    if (category === 'prescription') return 'bg-teal-50';
    if (category === 'lab_report') return 'bg-blue-50';
    return 'bg-slate-100';
  };

  const pendingReminders = remindersToday.filter(r => !r.is_completed && r.status !== 'COMPLETED');
  const mockReminders = pendingReminders.length === 0 ? [
    { id: 1, title: 'Take Azithromycin 500mg', time: 'Today • 8:00 PM', type: 'Medicine', typeColor: 'bg-blue-100 text-blue-700' },
    { id: 2, title: 'Eat fruits today 🍎', time: 'Today • Anytime', type: 'Nutrition', typeColor: 'bg-green-100 text-green-700' },
    { id: 3, title: 'Doctor Follow-up', time: 'Dec 01, 2026 • 10:00 AM', type: 'Appointment', typeColor: 'bg-purple-100 text-purple-700' },
  ] : pendingReminders.slice(0, 3).map(r => ({
    id: r.id,
    title: r.medicine_name || r.title || 'Reminder',
    time: r.scheduled_time || 'Today',
    type: r.reminder_type || 'Health',
    typeColor: 'bg-teal-100 text-teal-700',
  }));

  return (
    <div className="space-y-6">
      {/* Hero Banner */}
      <div
        className="rounded-2xl px-8 py-7 flex items-center justify-between overflow-hidden relative"
        style={{ background: 'linear-gradient(135deg, #0f2544 0%, #1a3a6e 100%)' }}
      >
        <div className="z-10">
          <h1 className="text-2xl font-extrabold text-white mb-1">
            Hello {firstName}! 👋
          </h1>
          <p className="text-blue-200 text-sm">Take control of your health with HealthMate AI</p>
        </div>
        <div className="absolute right-8 top-1/2 -translate-y-1/2 opacity-20 pointer-events-none">
          <Heart className="w-28 h-28 text-white" fill="currentColor" />
        </div>
        <div className="relative z-10 hidden sm:flex items-center space-x-3">
          <div className="w-16 h-16 rounded-full bg-white/10 flex items-center justify-center">
            <Heart className="w-8 h-8 text-red-400" fill="currentColor" />
          </div>
        </div>
      </div>

      {/* Quick Action Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {quickActions.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.title}
              onClick={action.onClick}
              className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md hover:border-teal-300 dark:hover:border-teal-700 transition-all text-left group"
            >
              <div className={`w-10 h-10 rounded-xl ${action.color} flex items-center justify-center mb-3`}>
                <Icon className={`w-5 h-5 ${action.iconColor}`} />
              </div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white leading-tight">{action.title}</h3>
              <p className="text-xs text-slate-500 mt-1 leading-snug">{action.desc}</p>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-teal-500 mt-2 transition-colors" />
            </button>
          );
        })}
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Health Overview + Recent Records */}
        <div className="lg:col-span-2 space-y-6">
          {/* Health Overview Card */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Heart className="w-5 h-5 text-rose-500" fill="currentColor" />
                Your Health Overview
              </h2>
              <Link to="/reports" className="text-xs font-semibold text-teal-600 hover:text-teal-700 flex items-center gap-1">
                View Details <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="flex flex-col sm:flex-row gap-6 items-start">
              {/* Status Circle */}
              <div className="flex flex-col items-center space-y-2 shrink-0">
                <div className="w-28 h-28 rounded-full border-4 border-teal-400 flex items-center justify-center bg-teal-50 dark:bg-teal-950/40">
                  <div className="text-center">
                    <Heart className="w-8 h-8 text-teal-500 mx-auto mb-1" />
                    <p className="text-sm font-extrabold text-teal-600">Healthy</p>
                  </div>
                </div>
                <div className="text-center">
                  <p className="text-[11px] text-slate-400">Last Updated</p>
                  <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1 justify-center">
                    <CheckCircle2 className="w-3 h-3 text-teal-500" /> All good!
                  </p>
                  <p className="text-[11px] text-slate-400">Keep up the good work.</p>
                </div>
              </div>

              {/* Trend Chart */}
              <div className="flex-1 h-40 w-full min-w-0">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={trendData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="healthGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#14b8a6" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#14b8a6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
                    <YAxis hide />
                    <Tooltip
                      contentStyle={{ background: '#0f172a', border: 'none', borderRadius: '0.75rem', fontSize: 12, color: '#f8fafc' }}
                    />
                    <Area type="monotone" dataKey="numeric_value" stroke="#14b8a6" strokeWidth={2.5} fill="url(#healthGrad)" dot={{ r: 3, fill: '#14b8a6' }} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Recent Medical Records */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-slate-900 dark:text-white">📂 Recent Medical Records</h2>
              <Link to="/records" className="text-xs font-semibold text-teal-600 hover:text-teal-700 flex items-center gap-1">
                View All <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-12 bg-slate-100 dark:bg-slate-800 rounded-xl animate-pulse" />
                ))}
              </div>
            ) : recentDocs.length === 0 ? (
              <div className="text-center py-8">
                <FileText className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="text-xs text-slate-500">No records yet. Upload your first document!</p>
                <button onClick={openUpload} className="mt-3 px-4 py-2 bg-teal-600 text-white text-xs font-bold rounded-xl">
                  Upload Record
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                {recentDocs.map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-lg ${getCategoryBg(doc.category)} flex items-center justify-center`}>
                        {getCategoryIcon(doc.category)}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-slate-900 dark:text-white truncate max-w-[200px]">{doc.title}</p>
                        <p className="text-xs text-slate-400">{doc.document_date || 'Recent'}</p>
                      </div>
                    </div>
                    <a
                      href={getApiUrl(`/documents/${doc.id}/download`)}
                      target="_blank"
                      rel="noreferrer"
                      className="p-1.5 text-slate-400 hover:text-teal-600 transition-colors"
                    >
                      <Download className="w-4 h-4" />
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right: Reminders + Nutrition */}
        <div className="space-y-6">
          {/* Upcoming Reminders */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Bell className="w-4 h-4 text-amber-500" />
                Upcoming Reminders
              </h2>
              <Link to="/appointments" className="text-xs font-semibold text-teal-600 hover:text-teal-700 flex items-center gap-1">
                View All <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="space-y-3">
              {mockReminders.map((rem) => (
                <div key={rem.id} className="flex items-start gap-3 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60">
                  <div className="w-8 h-8 rounded-lg bg-orange-100 dark:bg-orange-950/40 flex items-center justify-center shrink-0">
                    {rem.type === 'Medicine' ? <Pill className="w-4 h-4 text-orange-500" /> :
                     rem.type === 'Nutrition' ? <Utensils className="w-4 h-4 text-green-500" /> :
                     <Bell className="w-4 h-4 text-purple-500" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-slate-900 dark:text-white leading-tight">{rem.title}</p>
                    <p className="text-[11px] text-slate-400 mt-0.5">{rem.time}</p>
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full shrink-0 ${rem.typeColor}`}>
                    {rem.type}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Nutrition Suggestion */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-7 h-7 rounded-full bg-green-100 flex items-center justify-center">
                <span className="text-sm">🌿</span>
              </div>
              <h2 className="text-sm font-bold text-slate-900 dark:text-white">Nutrition Suggestion</h2>
            </div>

            <div className="flex gap-4 items-start">
              <div className="flex-1">
                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  Try to include more fresh fruits like apple, banana and orange in your daily diet.
                </p>
                <Link
                  to="/nutrition"
                  className="inline-flex items-center gap-1 mt-3 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl transition-all"
                >
                  Learn More <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
              <div className="shrink-0 text-3xl">🍎🍌🍊</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
