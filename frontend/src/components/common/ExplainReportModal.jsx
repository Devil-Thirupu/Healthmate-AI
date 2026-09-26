import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import {
  BotMessageSquare,
  Sparkles,
  ShieldCheck,
  Languages,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  X,
  ExternalLink
} from 'lucide-react';

const ExplainReportModal = ({ documentId, documentTitle, isOpen, onClose, onViewSource }) => {
  const [language, setLanguage] = useState('en'); // 'en', 'ta', 'tanglish'
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isOpen || !documentId) return;

    const fetchExplanation = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const res = await api.post(`/reports/${documentId}/explain`, {
          language: language
        });
        setData(res.data);
      } catch (err) {
        console.error('Failed to explain report:', err);
        setError(err.response?.data?.detail || 'Failed to generate grounded explanation.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchExplanation();
  }, [isOpen, documentId, language]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="w-full max-w-2xl bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200/90 dark:border-slate-800 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-5 bg-teal-600 text-white flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-white/20 backdrop-blur-xs flex items-center justify-center text-white">
              <BotMessageSquare className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-bold font-heading">Explain Diagnostic Report</h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-white/20 text-white">
                  Evidence Guarded
                </span>
              </div>
              <p className="text-[11px] text-teal-100 truncate max-w-md">
                {documentTitle || 'Diagnostic Lab Report'}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* Language Switcher */}
            <div className="flex items-center space-x-1 p-1 bg-black/20 rounded-xl text-xs font-semibold">
              <Languages className="w-3.5 h-3.5 ml-1 text-teal-200" />
              <button
                onClick={() => setLanguage('en')}
                className={`px-2 py-0.5 rounded-lg transition-colors ${
                  language === 'en' ? 'bg-white text-teal-800 font-bold' : 'text-white/80 hover:text-white'
                }`}
              >
                EN
              </button>
              <button
                onClick={() => setLanguage('ta')}
                className={`px-2 py-0.5 rounded-lg transition-colors ${
                  language === 'ta' ? 'bg-white text-teal-800 font-bold' : 'text-white/80 hover:text-white'
                }`}
              >
                தமிழ்
              </button>
              <button
                onClick={() => setLanguage('tanglish')}
                className={`px-2 py-0.5 rounded-lg transition-colors ${
                  language === 'tanglish' ? 'bg-white text-teal-800 font-bold' : 'text-white/80 hover:text-white'
                }`}
              >
                Multilanguage
              </button>
            </div>

            <button
              onClick={onClose}
              className="p-1 rounded-full hover:bg-white/20 text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {isLoading ? (
            <div className="py-16 text-center space-y-3">
              <Loader2 className="w-7 h-7 animate-spin text-teal-600 mx-auto" />
              <p className="text-xs font-bold text-slate-800 dark:text-slate-200">
                Synthesizing Evidence-Grounded Explanation...
              </p>
              <p className="text-[11px] text-slate-400">
                Verifying patient record citations and biological reference ranges
              </p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-center">
              <AlertTriangle className="w-6 h-6 text-rose-500 mx-auto mb-1" />
              <p className="text-xs font-bold text-rose-700">{error}</p>
            </div>
          ) : data ? (
            <div className="space-y-4">
              {/* Section 1: Overview */}
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700/60">
                <span className="text-[10px] font-bold uppercase tracking-wider text-teal-700 dark:text-teal-400">
                  Report Overview
                </span>
                <p className="text-xs text-slate-800 dark:text-slate-200 mt-1 font-medium leading-relaxed">
                  {data.report_overview}
                </p>
              </div>

              {/* Section 2: Recorded Values */}
              <div className="p-4 rounded-xl bg-teal-50/40 dark:bg-teal-950/30 border border-teal-200/50">
                <span className="text-[10px] font-bold uppercase tracking-wider text-teal-800 dark:text-teal-300">
                  Recorded Patient Values
                </span>
                <div className="text-xs text-slate-800 dark:text-slate-200 mt-1 font-mono whitespace-pre-line leading-relaxed">
                  {data.recorded_values_text}
                </div>
              </div>

              {/* Section 3: What Changed */}
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-600">
                  Historical Differences Observed
                </span>
                <div className="text-xs text-slate-800 dark:text-slate-200 mt-1 whitespace-pre-line leading-relaxed">
                  {data.what_changed_text}
                </div>
              </div>

              {/* Section 4: General Context */}
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Biomarker Clinical Context
                </span>
                <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 leading-relaxed">
                  {data.general_context_text}
                </p>
              </div>

              {/* Section 5: Disclaimer & Sources */}
              <div className="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 flex items-start space-x-2">
                <ShieldCheck className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <p className="text-[11px] text-amber-800 dark:text-amber-300 leading-relaxed">
                  <strong>Safety Notice:</strong> {data.disclaimer}
                </p>
              </div>

              {/* Sources footer */}
              <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800">
                <span className="text-xs text-slate-500 flex items-center space-x-1.5">
                  <FileText className="w-3.5 h-3.5 text-teal-600" />
                  <span>Source: {data.document_title}</span>
                </span>
                {onViewSource && (
                  <button
                    onClick={() => {
                      onClose();
                      onViewSource(data.document_id);
                    }}
                    className="text-xs font-bold text-teal-600 hover:text-teal-700 inline-flex items-center space-x-1"
                  >
                    <span>View Original File</span>
                    <ExternalLink className="w-3 h-3" />
                  </button>
                )}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};

export default ExplainReportModal;
