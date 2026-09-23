import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import {
  Calendar,
  Filter,
  Search,
  FlaskConical,
  Pill,
  FileText,
  Activity,
  CalendarCheck,
  TrendingUp,
  TrendingDown,
  Minus,
  ExternalLink,
  Loader2,
  ChevronDown,
  Sparkles
} from 'lucide-react';

const CATEGORIES = [
  { id: 'ALL', label: 'All Records' },
  { id: 'REPORTS', label: 'Reports', icon: FileText },
  { id: 'LAB_TESTS', label: 'Lab Tests', icon: FlaskConical },
  { id: 'PRESCRIPTIONS', label: 'Prescriptions', icon: Pill },
  { id: 'VITALS', label: 'Vitals', icon: Activity },
  { id: 'APPOINTMENTS', label: 'Appointments', icon: CalendarCheck },
];

const DATE_RANGES = [
  { id: 'all', label: 'All Time' },
  { id: '30d', label: 'Last 30 Days' },
  { id: '3m', label: 'Last 3 Months' },
  { id: '6m', label: 'Last 6 Months' },
  { id: '1y', label: 'Last Year' },
];

const HealthTimelineView = ({ onViewSource, onExplainReport }) => {
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [selectedDateRange, setSelectedDateRange] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [timelineData, setTimelineData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchTimeline = async () => {
    try {
      setIsLoading(true);
      const params = {
        category: selectedCategory,
        date_range: selectedDateRange
      };
      if (searchQuery.trim()) {
        params.q = searchQuery.trim();
      }

      const res = await api.get('/health-timeline', { params });
      setTimelineData(res.data);
    } catch (err) {
      console.error('Failed to load health timeline:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTimeline();
  }, [selectedCategory, selectedDateRange]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchTimeline();
  };

  const getEventIcon = (type) => {
    switch (type) {
      case 'REPORT':
        return <FileText className="w-4 h-4 text-teal-600" />;
      case 'LAB_TEST':
        return <FlaskConical className="w-4 h-4 text-teal-600" />;
      case 'PRESCRIPTION':
        return <Pill className="w-4 h-4 text-teal-600" />;
      case 'VITALS':
        return <Activity className="w-4 h-4 text-emerald-600" />;
      case 'APPOINTMENT':
        return <CalendarCheck className="w-4 h-4 text-sky-600" />;
      default:
        return <Activity className="w-4 h-4 text-slate-500" />;
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 p-6 shadow-2xs space-y-5">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-teal-50 dark:bg-teal-950 text-teal-600 flex items-center justify-center">
            <Calendar className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white font-heading">
              Smart Health Timeline
            </h3>
            <p className="text-[11px] text-slate-400">
              Chronological medical event stream synthesized across verified patient vault records
            </p>
          </div>
        </div>

        {/* Date Range Selector */}
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl text-xs font-semibold">
            {DATE_RANGES.map((dr) => (
              <button
                key={dr.id}
                onClick={() => setSelectedDateRange(dr.id)}
                className={`px-2.5 py-1 rounded-lg transition-colors ${
                  selectedDateRange === dr.id
                    ? 'bg-white dark:bg-slate-900 text-teal-700 dark:text-teal-300 font-bold shadow-2xs'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                {dr.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Category Pills & Search */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
          {CATEGORIES.map((cat) => {
            const Icon = cat.icon;
            const isSelected = selectedCategory === cat.id;
            return (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold shrink-0 flex items-center space-x-1.5 transition-all ${
                  isSelected
                    ? 'bg-teal-600 text-white shadow-xs'
                    : 'bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-300'
                }`}
              >
                {Icon && <Icon className="w-3.5 h-3.5" />}
                <span>{cat.label}</span>
              </button>
            );
          })}
        </div>

        {/* Search */}
        <form onSubmit={handleSearchSubmit} className="relative sm:w-64 shrink-0">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter timeline records..."
            className="w-full pl-8 pr-3.5 py-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/30"
          />
        </form>
      </div>

      {/* Timeline Stream */}
      {isLoading ? (
        <div className="py-16 text-center">
          <Loader2 className="w-6 h-6 animate-spin text-teal-600 mx-auto mb-2" />
          <p className="text-xs text-slate-400">Loading chronological timeline...</p>
        </div>
      ) : !timelineData || timelineData.events.length === 0 ? (
        <div className="p-10 text-center bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-dashed border-slate-200 dark:border-slate-700">
          <Calendar className="w-8 h-8 mx-auto mb-2 text-slate-300" />
          <p className="text-xs font-bold text-slate-700 dark:text-slate-300">No events matched your criteria</p>
          <p className="text-[10px] text-slate-400 mt-0.5">Try changing the category or date range filter.</p>
        </div>
      ) : (
        <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-200 dark:before:bg-slate-800">
          {timelineData.events.map((event) => (
            <div key={event.id} className="relative group">
              {/* Timeline Bullet */}
              <div className="absolute -left-6 top-3.5 w-5 h-5 rounded-full bg-white dark:bg-slate-900 border-2 border-teal-600 flex items-center justify-center text-[9px] shadow-2xs">
                <span className="w-2 h-2 rounded-full bg-teal-600"></span>
              </div>

              {/* Event Card */}
              <div className="bg-slate-50/70 hover:bg-white dark:bg-slate-800/60 dark:hover:bg-slate-800 rounded-xl p-4 border border-slate-200/80 dark:border-slate-700 hover:shadow-2xs transition-all">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-start space-x-3">
                    <div className="p-2 rounded-xl bg-white dark:bg-slate-900 shadow-2xs shrink-0">
                      {getEventIcon(event.event_type)}
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h4 className="text-xs font-bold text-slate-900 dark:text-white">
                          {event.title}
                        </h4>
                        <span className="text-[10px] font-semibold text-slate-400">
                          {event.event_date}
                        </span>
                      </div>

                      <p className="text-[11px] text-slate-600 dark:text-slate-300 mt-0.5">
                        {event.summary}
                      </p>

                      {/* Value / Trend */}
                      {event.relevant_value && (
                        <div className="flex items-center space-x-2 mt-2">
                          <span className="text-xs font-black text-slate-900 dark:text-white bg-white dark:bg-slate-900 px-2.5 py-0.5 rounded-md border border-slate-200 dark:border-slate-700">
                            {event.relevant_value} {event.unit || ''}
                          </span>

                          {event.trend_direction === 'Increased' ? (
                            <span className="inline-flex items-center text-[10px] font-bold text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950 px-2 py-0.5 rounded-full border border-amber-200">
                              <TrendingUp className="w-3 h-3 mr-0.5" />
                              {event.percentage_change || 'Increased'}
                            </span>
                          ) : event.trend_direction === 'Decreased' ? (
                            <span className="inline-flex items-center text-[10px] font-bold text-sky-700 dark:text-sky-300 bg-sky-50 dark:bg-sky-950 px-2 py-0.5 rounded-full border border-sky-200">
                              <TrendingDown className="w-3 h-3 mr-0.5" />
                              {event.percentage_change || 'Decreased'}
                            </span>
                          ) : event.previous_value ? (
                            <span className="inline-flex items-center text-[10px] font-bold text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950 px-2 py-0.5 rounded-full border border-emerald-200">
                              <Minus className="w-3 h-3 mr-0.5" />
                              Stable
                            </span>
                          ) : null}

                          {event.previous_value && (
                            <span className="text-[10px] text-slate-400">
                              (Prev: {event.previous_value})
                            </span>
                          )}
                        </div>
                      )}

                      {/* Source */}
                      {event.source_document_title && (
                        <div className="mt-2 text-[10px] text-slate-400 flex items-center space-x-1.5">
                          <FileText className="w-3 h-3 text-teal-600" />
                          <span>Source: {event.source_document_title}</span>
                          {event.source_document_id && onViewSource && (
                            <button
                              onClick={() => onViewSource(event.source_document_id)}
                              className="text-teal-600 dark:text-teal-400 hover:underline font-bold ml-1"
                            >
                              [View Source]
                            </button>
                          )}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions for reports */}
                  {event.event_type === 'REPORT' && event.source_document_id && onExplainReport && (
                    <button
                      onClick={() => onExplainReport(event.source_document_id, event.title)}
                      className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-teal-50 hover:bg-teal-100 text-teal-800 text-xs font-bold shrink-0 self-end sm:self-center transition-colors border border-teal-200/60"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Explain Report</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default HealthTimelineView;
