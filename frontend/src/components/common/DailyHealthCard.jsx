import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import {
  Activity,
  Pill,
  TrendingUp,
  TrendingDown,
  Minus,
  Apple,
  CalendarCheck,
  FileText,
  Clock,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Sparkles
} from 'lucide-react';

const DailyHealthCard = () => {
  const [insights, setInsights] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchDailyInsights = async () => {
    try {
      setIsLoading(true);
      const res = await api.get('/reminders/daily-insights');
      setInsights(res.data);
    } catch (err) {
      console.error('Error fetching daily health insights:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDailyInsights();
    const handleUpdate = () => fetchDailyInsights();
    window.addEventListener('healthmate_reminder_updated', handleUpdate);
    window.addEventListener('healthmate_doc_uploaded', handleUpdate);
    return () => {
      window.removeEventListener('healthmate_reminder_updated', handleUpdate);
      window.removeEventListener('healthmate_doc_uploaded', handleUpdate);
    };
  }, []);

  if (isLoading || !insights) {
    return (
      <div className="animate-pulse bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200/90 dark:border-slate-800">
        <div className="h-5 bg-slate-200 dark:bg-slate-800 rounded w-1/4 mb-4"></div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="h-28 bg-slate-100 dark:bg-slate-800 rounded-xl"></div>
          <div className="h-28 bg-slate-100 dark:bg-slate-800 rounded-xl"></div>
          <div className="h-28 bg-slate-100 dark:bg-slate-800 rounded-xl"></div>
          <div className="h-28 bg-slate-100 dark:bg-slate-800 rounded-xl"></div>
        </div>
      </div>
    );
  }

  const primaryBiomarker = insights.latest_biomarkers?.[0];

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 p-6 shadow-2xs">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-teal-50 dark:bg-teal-950 text-teal-600 flex items-center justify-center">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider font-heading">
              Today's Clinical Synthesis & Daily Targets
            </h2>
            <p className="text-[11px] text-slate-400">
              Personalized daily snapshot synthesized from verified records & USDA nutrition intelligence
            </p>
          </div>
        </div>
        <span className="text-xs font-bold px-3 py-1 rounded-full bg-teal-50 dark:bg-teal-950/60 text-teal-800 dark:text-teal-300 border border-teal-200/50">
          {new Date().toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}
        </span>
      </div>

      {/* Grid of Daily Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Medications */}
        <div className="bg-slate-50/70 dark:bg-slate-800/60 rounded-xl p-4 border border-slate-200/60 dark:border-slate-800/80 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Prescription Doses
              </span>
              <div className="w-7 h-7 rounded-lg bg-teal-50 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center">
                <Pill className="w-4 h-4" />
              </div>
            </div>

            <div className="mt-1">
              <p className="text-2xl font-black text-slate-900 dark:text-white font-heading">
                {insights.reminders_remaining_today}{' '}
                <span className="text-xs font-semibold text-slate-500">remaining</span>
              </p>
              <p className="text-[11px] text-emerald-600 dark:text-emerald-400 font-bold mt-0.5">
                ✓ {insights.reminders_completed_today} completed today
              </p>
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-slate-200/60 dark:border-slate-700/60">
            <Link
              to="/prescriptions"
              className="text-[11px] font-bold text-teal-600 hover:text-teal-700 dark:text-teal-400 flex items-center justify-between"
            >
              <span>Manage schedule</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>

        {/* Card 2: Latest Biomarker */}
        <div className="bg-slate-50/70 dark:bg-slate-800/60 rounded-xl p-4 border border-slate-200/60 dark:border-slate-800/80 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 truncate">
                {primaryBiomarker ? primaryBiomarker.test_name : 'Latest Measurement'}
              </span>
              <div className="w-7 h-7 rounded-lg bg-teal-50 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center">
                <Activity className="w-4 h-4" />
              </div>
            </div>

            {primaryBiomarker ? (
              <div className="mt-1">
                <p className="text-2xl font-black text-slate-900 dark:text-white font-heading">
                  {primaryBiomarker.latest_value}{' '}
                  <span className="text-xs font-semibold text-slate-500">{primaryBiomarker.unit}</span>
                </p>
                <div className="flex items-center space-x-1.5 mt-1 text-[11px]">
                  {primaryBiomarker.trend_direction === 'Increased' ? (
                    <span className="inline-flex items-center text-amber-600 dark:text-amber-400 font-bold">
                      <TrendingUp className="w-3 h-3 mr-0.5" />
                      {primaryBiomarker.percentage_change || 'Elevated'}
                    </span>
                  ) : primaryBiomarker.trend_direction === 'Decreased' ? (
                    <span className="inline-flex items-center text-sky-600 dark:text-sky-400 font-bold">
                      <TrendingDown className="w-3 h-3 mr-0.5" />
                      {primaryBiomarker.percentage_change || 'Reduced'}
                    </span>
                  ) : (
                    <span className="inline-flex items-center text-emerald-600 dark:text-emerald-400 font-bold">
                      <Minus className="w-3 h-3 mr-0.5" />
                      Optimal range
                    </span>
                  )}
                  {primaryBiomarker.date && (
                    <span className="text-slate-400">({primaryBiomarker.date})</span>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-400 mt-2">No recent lab tests found.</p>
            )}
          </div>

          <div className="mt-3 pt-3 border-t border-slate-200/60 dark:border-slate-700/60">
            <Link
              to="/reports"
              className="text-[11px] font-bold text-teal-600 hover:text-teal-700 dark:text-teal-400 flex items-center justify-between"
            >
              <span>View lab trends</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>

        {/* Card 3: Daily USDA Nutrition */}
        <div className="bg-slate-50/70 dark:bg-slate-800/60 rounded-xl p-4 border border-slate-200/60 dark:border-slate-800/80 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                USDA Nutrition Intake
              </span>
              <div className="w-7 h-7 rounded-lg bg-teal-50 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center">
                <Apple className="w-4 h-4" />
              </div>
            </div>

            {insights.nutrition_ideas && insights.nutrition_ideas.length > 0 ? (
              <div className="mt-1">
                <p className="text-sm font-bold text-slate-900 dark:text-white truncate">
                  {insights.nutrition_ideas[0].common_name || insights.nutrition_ideas[0].food_name}
                </p>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                  {insights.nutrition_ideas[0].calories} kcal • {insights.nutrition_ideas[0].fiber_g}g fiber • {insights.nutrition_ideas[0].carbohydrate_g}g carbs
                </p>
                <p className="text-[10px] text-teal-700 dark:text-teal-400 mt-1 font-semibold">
                  Source: USDA FoodData Central
                </p>
              </div>
            ) : (
              <p className="text-xs text-slate-400 mt-2">USDA Nutrition Intelligence active.</p>
            )}
          </div>

          <div className="mt-3 pt-3 border-t border-slate-200/60 dark:border-slate-700/60">
            <Link
              to="/nutrition"
              className="text-[11px] font-bold text-teal-600 hover:text-teal-700 dark:text-teal-400 flex items-center justify-between"
            >
              <span>Explore food database</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>

        {/* Card 4: Doctor Visit Prep */}
        <div className="bg-slate-50/70 dark:bg-slate-800/60 rounded-xl p-4 border border-slate-200/60 dark:border-slate-800/80 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Doctor Visit Brief
              </span>
              <div className="w-7 h-7 rounded-lg bg-teal-50 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center">
                <CalendarCheck className="w-4 h-4" />
              </div>
            </div>

            <div className="mt-1">
              <p className="text-sm font-bold text-slate-900 dark:text-white">
                Summary & PDF Ready
              </p>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                Generate trilingual visit questions and clinical briefing sheets.
              </p>
            </div>
          </div>

          <div className="mt-3 pt-3 border-t border-slate-200/60 dark:border-slate-700/60">
            <Link
              to="/appointment-prep"
              className="text-[11px] font-bold text-teal-600 hover:text-teal-700 dark:text-teal-400 flex items-center justify-between"
            >
              <span>Prepare appointment</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DailyHealthCard;
