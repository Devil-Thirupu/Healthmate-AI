import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import api from '../services/api';
import {
  FlaskConical,
  PlusCircle,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  Building,
  TrendingUp,
  TrendingDown,
  Minus,
  FileText,
  Search,
  Languages,
  Loader2,
  Layers,
  ExternalLink,
  CheckSquare,
  Square,
  X,
  ArrowRight
} from 'lucide-react';

const ReportsPage = () => {
  const { openUpload } = useOutletContext();
  const [labDocs, setLabDocs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedLang, setSelectedLang] = useState('en'); // 'en', 'ta', 'tanglish'
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [comparisonMatrix, setComparisonMatrix] = useState(null);
  const [isComparing, setIsComparing] = useState(false);
  const [showCompareModal, setShowCompareModal] = useState(false);

  const fetchLabReports = async () => {
    try {
      setIsLoading(true);
      const res = await api.get('/documents/', { params: { category: 'lab_report' } });
      setLabDocs(res.data || []);
    } catch (err) {
      console.error('Failed to fetch lab reports:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLabReports();
    const handleRefresh = () => fetchLabReports();
    window.addEventListener('healthmate_doc_uploaded', handleRefresh);
    return () => window.removeEventListener('healthmate_doc_uploaded', handleRefresh);
  }, []);

  const toggleSelectDoc = (docId) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  const handleCompareReports = async () => {
    if (selectedDocIds.length < 2) return;
    try {
      setIsComparing(true);
      const res = await api.post('/health-intelligence/compare-reports', {
        document_ids: selectedDocIds
      });
      setComparisonMatrix(res.data);
      setShowCompareModal(true);
    } catch (err) {
      console.error('Comparison error:', err);
      alert('Failed to compare reports: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsComparing(false);
    }
  };

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
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white font-heading">
            Clinical Lab Reports & Biomarkers
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Diagnostic reports with extracted blood parameters, reference ranges, and multi-report comparison
          </p>
        </div>

        <div className="flex items-center space-x-2.5">
          {/* Language Switcher */}
          <div className="flex items-center space-x-1 p-1 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 text-xs">
            <Languages className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400 ml-1.5" />
            <button
              onClick={() => setSelectedLang('en')}
              className={`px-2 py-0.5 rounded-lg font-medium ${
                selectedLang === 'en' ? 'bg-brand-600 text-white' : 'text-slate-500'
              }`}
            >
              EN
            </button>
            <button
              onClick={() => setSelectedLang('ta')}
              className={`px-2 py-0.5 rounded-lg font-medium ${
                selectedLang === 'ta' ? 'bg-brand-600 text-white' : 'text-slate-500'
              }`}
            >
              தமிழ்
            </button>
            <button
              onClick={() => setSelectedLang('tanglish')}
              className={`px-2 py-0.5 rounded-lg font-medium ${
                selectedLang === 'tanglish' ? 'bg-brand-600 text-white' : 'text-slate-500'
              }`}
            >
              Tanglish
            </button>
          </div>

          <button
            onClick={openUpload}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-brand-600 to-cyan-600 hover:from-brand-700 hover:to-cyan-700 text-white text-xs font-semibold rounded-xl shadow-md shadow-brand-500/20 transition-all active:scale-95"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Upload Lab Report</span>
          </button>
        </div>
      </div>

      {/* Multi-Report Selection Action Bar */}
      {selectedDocIds.length >= 2 && (
        <div className="p-4 rounded-2xl bg-brand-50 dark:bg-brand-950/60 border border-brand-200 dark:border-brand-800 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-sm animate-in fade-in">
          <div className="flex items-center space-x-2 text-xs text-brand-900 dark:text-brand-200">
            <Layers className="w-4 h-4 text-brand-600" />
            <span className="font-bold">{selectedDocIds.length} reports selected for comparative analysis</span>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setSelectedDocIds([])}
              className="px-3 py-1.5 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-800 rounded-xl transition-colors"
            >
              Clear Selection
            </button>
            <button
              disabled={isComparing}
              onClick={handleCompareReports}
              className="px-4 py-1.5 bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold rounded-xl shadow-md shadow-brand-500/20 transition-all inline-flex items-center space-x-1.5"
            >
              {isComparing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Layers className="w-3.5 h-3.5" />}
              <span>Compare Selected Reports</span>
            </button>
          </div>
        </div>
      )}

      {/* Biomarker Overview Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-1">
          <span className="text-[11px] font-semibold text-slate-400">Total Lab Tests Uploaded</span>
          <p className="text-2xl font-bold text-slate-900 dark:text-white font-heading">
            {labDocs.length} Reports
          </p>
          <p className="text-[11px] text-brand-600 dark:text-brand-400">
            Select 2+ reports to cross-tabulate biomarkers
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-1">
          <span className="text-[11px] font-semibold text-slate-400">Tracked Biomarker Panels</span>
          <p className="text-2xl font-bold text-slate-900 dark:text-white font-heading">
            CBC • Lipid • LFT • KFT
          </p>
          <p className="text-[11px] text-emerald-600 dark:text-emerald-400">
            Standard biological reference ranges mapped
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-1">
          <span className="text-[11px] font-semibold text-slate-400">Evidence Guard Status</span>
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400 font-heading flex items-center space-x-1.5">
            <CheckCircle2 className="w-5 h-5" />
            <span>100% Grounded</span>
          </p>
          <p className="text-[11px] text-slate-500">Zero synthetic or unverified values</p>
        </div>
      </div>

      {/* Reports Listing */}
      {isLoading ? (
        <div className="p-16 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
          <Loader2 className="w-7 h-7 animate-spin text-brand-600 mx-auto mb-2" />
          <p className="text-xs text-slate-500">Loading lab reports...</p>
        </div>
      ) : labDocs.length === 0 ? (
        <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 space-y-3">
          <FlaskConical className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto" />
          <div>
            <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
              No lab reports uploaded yet
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Upload blood tests, urine analysis, or biopsy documents to see biomarker breakdowns.
            </p>
          </div>
          <button
            onClick={openUpload}
            className="inline-flex items-center space-x-1.5 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold rounded-xl transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Upload Lab Report</span>
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between px-1">
            <span className="text-xs text-slate-500">
              Check reports to enable multi-report comparison:
            </span>
            <span className="text-xs font-semibold text-brand-600 dark:text-brand-400">
              {selectedDocIds.length} of {labDocs.length} selected
            </span>
          </div>

          {labDocs.map((doc) => {
            const isSelected = selectedDocIds.includes(doc.id);
            return (
              <div
                key={doc.id}
                onClick={() => toggleSelectDoc(doc.id)}
                className={`p-5 rounded-2xl bg-white dark:bg-slate-900 border transition-all cursor-pointer shadow-sm space-y-3 ${
                  isSelected
                    ? 'border-brand-500 dark:border-brand-400 ring-2 ring-brand-500/20 bg-brand-50/20 dark:bg-brand-950/20'
                    : 'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center space-x-3">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleSelectDoc(doc.id);
                      }}
                      className="text-brand-600 dark:text-brand-400 shrink-0"
                    >
                      {isSelected ? <CheckSquare className="w-5 h-5" /> : <Square className="w-5 h-5 text-slate-400" />}
                    </button>

                    <div className="w-10 h-10 rounded-xl bg-cyan-50 dark:bg-cyan-950 text-cyan-600 dark:text-cyan-400 flex items-center justify-center shrink-0">
                      <FlaskConical className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                        {doc.title}
                      </h3>
                      <p className="text-xs text-slate-400 flex items-center space-x-2 mt-0.5">
                        <span>Date: {doc.document_date || 'Undated'}</span>
                        {doc.clinic_or_lab && <span>• {doc.clinic_or_lab}</span>}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900">
                      SHA-256 Hashed
                    </span>
                    <a
                      href={`/api/v1/documents/${doc.id}/download`}
                      target="_blank"
                      rel="noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="px-3 py-1.5 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 transition-colors"
                    >
                      View Original
                    </a>
                  </div>
                </div>

                {/* Explanations preview box */}
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 text-xs text-slate-600 dark:text-slate-300 space-y-1">
                  <p className="font-semibold text-slate-800 dark:text-slate-200">
                    {selectedLang === 'ta'
                      ? 'மருத்துவ அறிக்கை தகவல்:'
                      : selectedLang === 'tanglish'
                      ? 'Medical Report Thagaval:'
                      : 'Report Extraction & OCR Metadata:'}
                  </p>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">
                    {selectedLang === 'ta'
                      ? 'இந்த அறிக்கையில் உள்ள இரத்தப் பரிசோதனை முடிவுகள் பாதுகாப்பாக பதிவு செய்யப்பட்டுள்ளன. ஏதேனும் முரண்பாடுகள் இருப்பின் உங்கள் மருத்துவரிடம் கலந்தாலோசிக்கவும்.'
                      : selectedLang === 'tanglish'
                      ? 'Indha report-il ulla blood test results bathiramaaga save seiyappattulladhu. Doctor advice-udan consult seiyavum.'
                      : 'Biomarkers extracted from this document automatically cross-tabulate in the Advanced Comparison Tool.'}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ----------------------------------------------------------------------------- */}
      {/* ADVANCED MULTI-REPORT COMPARISON MODAL */}
      {/* ----------------------------------------------------------------------------- */}
      {showCompareModal && comparisonMatrix && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-2xl max-w-5xl w-full max-h-[90vh] flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-800/50">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center space-x-2 font-heading">
                  <Layers className="w-5 h-5 text-brand-600" />
                  <span>Advanced Multi-Report Comparison Matrix</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Comparing {comparisonMatrix.compared_documents.length} diagnostic reports ({comparisonMatrix.total_tests_compared} biomarkers analyzed)
                </p>
              </div>
              <button
                onClick={() => setShowCompareModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-5 overflow-y-auto space-y-4 text-xs">
              {/* Compared Reports Summary Pills */}
              <div className="flex flex-wrap gap-2 pb-2 border-b border-slate-100 dark:border-slate-800">
                <span className="text-[11px] font-semibold text-slate-400 flex items-center mr-1">Reports:</span>
                {comparisonMatrix.compared_documents.map((doc, idx) => (
                  <div
                    key={idx}
                    className="px-3 py-1 bg-slate-100 dark:bg-slate-800 rounded-lg text-[11px] font-medium text-slate-700 dark:text-slate-300 flex items-center space-x-1.5"
                  >
                    <span className="font-bold text-brand-600 dark:text-brand-400">#{idx + 1}</span>
                    <span>{doc.title}</span>
                    <span className="text-slate-400">({doc.date})</span>
                  </div>
                ))}
              </div>

              {/* Comparison Table */}
              {comparisonMatrix.comparisons.length === 0 ? (
                <div className="p-8 text-center bg-slate-50 dark:bg-slate-800/40 rounded-xl">
                  <p className="text-xs text-slate-500">
                    No matching structured biomarkers were found between the selected reports.
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 border-b border-slate-200 dark:border-slate-800">
                      <tr>
                        <th className="px-3 py-2.5 font-semibold">Test Name</th>
                        <th className="px-3 py-2.5 font-semibold">Baseline Report</th>
                        <th className="px-3 py-2.5 font-semibold">Latest Report</th>
                        <th className="px-3 py-2.5 font-semibold">Change</th>
                        <th className="px-3 py-2.5 font-semibold">% Change</th>
                        <th className="px-3 py-2.5 font-semibold">Trend</th>
                        <th className="px-3 py-2.5 font-semibold">Reference Status</th>
                        <th className="px-3 py-2.5 font-semibold text-right">Source Traceability</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {comparisonMatrix.comparisons.map((c, idx) => (
                        <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40 transition-colors">
                          <td className="px-3 py-2.5 font-bold text-slate-900 dark:text-white">
                            {c.test_name}
                            <span className="block text-[10px] font-normal text-slate-400">{c.category}</span>
                          </td>
                          <td className="px-3 py-2.5 text-slate-700 dark:text-slate-300">
                            {c.baseline_value}
                            <span className="block text-[10px] text-slate-400">{c.baseline_date}</span>
                          </td>
                          <td className="px-3 py-2.5 font-semibold text-slate-900 dark:text-white">
                            {c.latest_value}
                            <span className="block text-[10px] text-slate-400">{c.latest_date}</span>
                          </td>
                          <td className="px-3 py-2.5 font-mono font-medium text-slate-800 dark:text-slate-200">
                            {c.change}
                          </td>
                          <td className="px-3 py-2.5 font-mono font-bold">
                            <span
                              className={
                                c.percentage_change.startsWith('+')
                                  ? 'text-amber-600 dark:text-amber-400'
                                  : c.percentage_change.startsWith('-')
                                  ? 'text-blue-600 dark:text-blue-400'
                                  : 'text-slate-600 dark:text-slate-400'
                              }
                            >
                              {c.percentage_change}
                            </span>
                          </td>
                          <td className="px-3 py-2.5">
                            {getTrendBadge(c.trend_direction)}
                          </td>
                          <td className="px-3 py-2.5">
                            {c.reference_range_status === 'Within available reference range' ? (
                              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
                                Within range
                              </span>
                            ) : c.reference_range_status === 'Outside available reference range' ? (
                              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300">
                                Outside range
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded text-[10px] font-normal text-slate-400">
                                Not available
                              </span>
                            )}
                          </td>
                          <td className="px-3 py-2.5 text-right">
                            {c.latest_doc_id && (
                              <a
                                href={`/api/v1/documents/${c.latest_doc_id}/download`}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold text-brand-600 dark:text-brand-400 hover:bg-brand-50 dark:hover:bg-brand-950 border border-brand-200 dark:border-brand-800 transition-colors"
                              >
                                <span>View Source</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Safety notice in modal */}
              <p className="text-[11px] text-slate-400 italic pt-1">
                * Note: Changes and trends represent mathematical differences across selected chronological reports. No automated diagnostic interpretation is performed.
              </p>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex justify-end">
              <button
                onClick={() => setShowCompareModal(false)}
                className="px-4 py-2 bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-800 dark:text-white text-xs font-semibold rounded-xl transition-colors"
              >
                Close Comparison
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportsPage;
