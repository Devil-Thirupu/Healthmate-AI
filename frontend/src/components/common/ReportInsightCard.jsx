import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import {
  FileText,
  TrendingUp,
  TrendingDown,
  Minus,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles
} from 'lucide-react';

const ReportInsightCard = ({ documentId }) => {
  const [cardData, setCardData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!documentId) return;

    const fetchReportInsights = async () => {
      try {
        setIsLoading(true);
        const res = await api.get(`/reminders/report-insights/${documentId}`);
        setCardData(res.data);
      } catch (err) {
        console.error('Error fetching report insights:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchReportInsights();
  }, [documentId]);

  if (isLoading || !cardData || cardData.total_measurements_extracted === 0) {
    return null;
  }

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200/90 dark:border-slate-800 shadow-2xs mb-6">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-teal-50 dark:bg-teal-950 text-teal-600 flex items-center justify-center">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider font-heading">
              Report Insights & Cross-Comparisons
            </h3>
            <p className="text-[11px] text-slate-400">
              {cardData.document_title} • {cardData.document_date || 'Recent Diagnostic'}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-[10px] font-bold">
          <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/60 dark:bg-emerald-950 dark:text-emerald-300">
            ✓ {cardData.total_measurements_extracted} Extracted
          </span>
          {cardData.measurements_with_comparison > 0 && (
            <span className="px-2.5 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200/60 dark:bg-teal-950 dark:text-teal-300">
              ✓ {cardData.measurements_with_comparison} Compared
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
        {cardData.insights.map((item, idx) => (
          <div
            key={idx}
            className="bg-slate-50/70 dark:bg-slate-800/80 rounded-xl p-3.5 border border-slate-200/60 dark:border-slate-700"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-800 dark:text-slate-200 truncate">
                {item.test_name}
              </span>
              {item.trend_direction === 'Increased' ? (
                <span className="inline-flex items-center text-[10px] font-bold text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950 px-1.5 py-0.5 rounded-full border border-amber-200">
                  <TrendingUp className="w-3 h-3 mr-0.5" />
                  {item.percentage_change || '↑'}
                </span>
              ) : item.trend_direction === 'Decreased' ? (
                <span className="inline-flex items-center text-[10px] font-bold text-sky-700 dark:text-sky-400 bg-sky-50 dark:bg-sky-950 px-1.5 py-0.5 rounded-full border border-sky-200">
                  <TrendingDown className="w-3 h-3 mr-0.5" />
                  {item.percentage_change || '↓'}
                </span>
              ) : item.has_previous_comparison ? (
                <span className="inline-flex items-center text-[10px] font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950 px-1.5 py-0.5 rounded-full border border-emerald-200">
                  <Minus className="w-3 h-3 mr-0.5" />
                  Optimal
                </span>
              ) : (
                <span className="text-[10px] font-semibold text-slate-400 bg-white dark:bg-slate-700 px-1.5 py-0.5 rounded-full border border-slate-200">
                  Baseline
                </span>
              )}
            </div>

            <div className="mt-2 flex items-baseline justify-between">
              <p className="text-base font-black text-slate-900 dark:text-white font-heading">
                {item.latest_value} <span className="text-[10px] font-normal text-slate-400">{item.unit || ''}</span>
              </p>
              {item.has_previous_comparison && (
                <p className="text-[10px] text-slate-400">
                  Prev: {item.previous_value} {item.unit || ''}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ReportInsightCard;
