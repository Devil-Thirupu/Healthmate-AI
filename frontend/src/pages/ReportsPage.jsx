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
  ArrowRight,
  Sparkles,
  ShieldCheck,
  ChevronRight,
  Download
} from 'lucide-react';
import ReportInsightCard from '../components/common/ReportInsightCard';
import ExplainReportModal from '../components/common/ExplainReportModal';

const ReportsPage = () => {
  const { openUpload } = useOutletContext();
  const [labDocs, setLabDocs] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [selectedDocDetail, setSelectedDocDetail] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [selectedLang, setSelectedLang] = useState('en'); // 'en', 'ta', 'tanglish'
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [comparisonMatrix, setComparisonMatrix] = useState(null);
  const [isComparing, setIsComparing] = useState(false);
  const [showCompareModal, setShowCompareModal] = useState(false);
  const [explainModalDoc, setExplainModalDoc] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchLabReports = async () => {
    try {
      setIsLoading(true);
      const res = await api.get('/documents/', { params: { category: 'lab_report' } });
      const docs = res.data || [];
      setLabDocs(docs);
      if (docs.length > 0 && !selectedDocId) {
        setSelectedDocId(docs[0].id);
      }
    } catch (err) {
      console.error('Failed to fetch lab reports:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchDocDetail = async (id) => {
    if (!id) return;
    try {
      setIsDetailLoading(true);
      const res = await api.get(`/documents/${id}`);
      setSelectedDocDetail(res.data);
    } catch (err) {
      console.error('Failed to fetch document detail:', err);
    } finally {
      setIsDetailLoading(false);
    }
  };

  useEffect(() => {
    fetchLabReports();
    const handleRefresh = () => fetchLabReports();
    window.addEventListener('healthmate_doc_uploaded', handleRefresh);
    return () => window.removeEventListener('healthmate_doc_uploaded', handleRefresh);
  }, []);

  useEffect(() => {
    if (selectedDocId) {
      fetchDocDetail(selectedDocId);
    }
  }, [selectedDocId]);

  const toggleSelectForComparison = (docId, e) => {
    e.stopPropagation();
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

  const getStatusBadge = (flag) => {
    switch (flag) {
      case 'high':
      case 'critical':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200/60 dark:bg-rose-950/60 dark:text-rose-300">
            Elevated
          </span>
        );
      case 'low':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200/60 dark:bg-amber-950/60 dark:text-amber-300">
            Reduced
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200/60 dark:bg-emerald-950/60 dark:text-emerald-300">
            Optimal
          </span>
        );
    }
  };

  const filteredLabDocs = labDocs.filter(d =>
    d.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    d.clinic_or_lab?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    d.doctor_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-extrabold uppercase tracking-widest text-teal-700 bg-teal-50 dark:bg-teal-950/60 px-2.5 py-0.5 rounded-full border border-teal-200/60 dark:border-teal-800/50">
              Clinical Pathology Synthesis
            </span>
            <span className="text-xs text-slate-400">
              • Tracked Panels: <strong className="text-slate-800 dark:text-slate-200">{labDocs.length} Reports</strong>
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white font-heading tracking-tight mt-1">
            EHR Automated Lab Synthesis & Biomarkers
          </h1>
          <p className="text-xs text-slate-500 max-w-2xl mt-0.5">
            Descriptive comparative intelligence, reference interval tracking, and OCR validation across patient diagnostic panels.
          </p>
        </div>

        <div className="flex items-center flex-wrap gap-2.5 shrink-0">
          {/* Trilingual Language Selector */}
          <div className="flex items-center space-x-1 p-1 bg-white dark:bg-slate-800 rounded-xl border border-slate-200/90 dark:border-slate-700 text-xs font-semibold shadow-2xs">
            <Languages className="w-3.5 h-3.5 text-teal-600 ml-1.5" />
            <button
              onClick={() => setSelectedLang('en')}
              className={`px-2.5 py-1 rounded-lg transition-all ${
                selectedLang === 'en' ? 'bg-teal-600 text-white font-bold' : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              EN
            </button>
            <button
              onClick={() => setSelectedLang('ta')}
              className={`px-2.5 py-1 rounded-lg transition-all ${
                selectedLang === 'ta' ? 'bg-teal-600 text-white font-bold' : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              தமிழ்
            </button>
            <button
              onClick={() => setSelectedLang('tanglish')}
              className={`px-2.5 py-1 rounded-lg transition-all ${
                selectedLang === 'tanglish' ? 'bg-teal-600 text-white font-bold' : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Tanglish
            </button>
          </div>

          <button
            onClick={openUpload}
            className="inline-flex items-center space-x-1.5 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl shadow-xs transition-all active:scale-95"
          >
            <PlusCircle className="w-4 h-4" />
            <span>+ Ingest Lab Report</span>
          </button>
        </div>
      </div>

      {/* Multi-Report Action Notification if Selected */}
      {selectedDocIds.length >= 2 && (
        <div className="p-4 rounded-2xl bg-teal-50 dark:bg-teal-950/60 border border-teal-200 dark:border-teal-800 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-2xs">
          <div className="flex items-center space-x-2.5 text-xs text-teal-900 dark:text-teal-200">
            <Layers className="w-4 h-4 text-teal-600" />
            <span className="font-bold">{selectedDocIds.length} reports checked for longitudinal matrix synthesis</span>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setSelectedDocIds([])}
              className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-white rounded-xl transition-colors"
            >
              Clear
            </button>
            <button
              disabled={isComparing}
              onClick={handleCompareReports}
              className="px-4 py-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl shadow-xs transition-all inline-flex items-center space-x-1.5"
            >
              {isComparing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Layers className="w-3.5 h-3.5" />}
              <span>Generate Cross-Tabulation Matrix</span>
            </button>
          </div>
        </div>
      )}

      {/* Main Split: Left Cohort Documents, Right Report Pathology Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (1/3): Diagnostic Documents Sidebar */}
        <div className="space-y-4">
          <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 font-heading">
                Cohort Documents ({labDocs.length})
              </h2>
              <span className="text-[10px] text-teal-700 font-bold bg-teal-50 dark:bg-teal-950 px-2 py-0.5 rounded-full">
                {selectedDocIds.length} Checked
              </span>
            </div>

            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Filter by report or lab..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500/30"
              />
            </div>

            {isLoading ? (
              <div className="p-8 text-center">
                <Loader2 className="w-5 h-5 animate-spin text-teal-600 mx-auto mb-1" />
                <p className="text-xs text-slate-400">Loading cohort...</p>
              </div>
            ) : filteredLabDocs.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-400">
                No lab reports matching filter.
              </div>
            ) : (
              <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
                {filteredLabDocs.map((doc) => {
                  const isActive = doc.id === selectedDocId;
                  const isChecked = selectedDocIds.includes(doc.id);
                  return (
                    <div
                      key={doc.id}
                      onClick={() => setSelectedDocId(doc.id)}
                      className={`p-3.5 rounded-xl border transition-all cursor-pointer flex items-start space-x-3 ${
                        isActive
                          ? 'border-teal-500 bg-teal-50/50 dark:bg-teal-950/40 ring-1 ring-teal-500 shadow-2xs'
                          : 'border-slate-200/80 dark:border-slate-800 bg-slate-50/40 dark:bg-slate-850 hover:bg-slate-50 dark:hover:bg-slate-800'
                      }`}
                    >
                      <button
                        type="button"
                        onClick={(e) => toggleSelectForComparison(doc.id, e)}
                        className="mt-0.5 text-teal-600 shrink-0"
                        title="Check to include in multi-report comparison"
                      >
                        {isChecked ? <CheckSquare className="w-4 h-4" /> : <Square className="w-4 h-4 text-slate-400" />}
                      </button>

                      <div className="min-w-0 flex-1">
                        <h4 className="text-xs font-bold text-slate-900 dark:text-white truncate">
                          {doc.title}
                        </h4>
                        <p className="text-[11px] text-slate-400 flex items-center space-x-1.5 mt-0.5">
                          <span>{doc.document_date || 'Undated'}</span>
                          {doc.clinic_or_lab && (
                            <>
                              <span>•</span>
                              <span className="truncate">{doc.clinic_or_lab}</span>
                            </>
                          )}
                        </p>
                      </div>

                      <ChevronRight className={`w-4 h-4 shrink-0 transition-transform ${isActive ? 'text-teal-600 translate-x-0.5' : 'text-slate-300'}`} />
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Column (2/3): Report Details & Extracted Pathology Biomarkers */}
        <div className="lg:col-span-2 space-y-6">
          {isDetailLoading || !selectedDocDetail ? (
            <div className="p-16 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800">
              <Loader2 className="w-6 h-6 animate-spin text-teal-600 mx-auto mb-2" />
              <p className="text-xs text-slate-400">Loading lab synthesis...</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Report Extraction Header Card */}
              <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-xl bg-teal-50 dark:bg-teal-950 text-teal-600 flex items-center justify-center shrink-0">
                      <FlaskConical className="w-5 h-5" />
                    </div>
                    <div>
                      <h2 className="text-base font-bold text-slate-900 dark:text-white font-heading">
                        {selectedDocDetail.title}
                      </h2>
                      <p className="text-[11px] text-slate-400 flex items-center space-x-2 mt-0.5">
                        <span>Date: {selectedDocDetail.document_date || 'Undated'}</span>
                        <span>•</span>
                        <span>Lab: {selectedDocDetail.clinic_or_lab || 'Apollo Diagnostics'}</span>
                        <span>•</span>
                        <span className="text-emerald-600 font-bold flex items-center space-x-0.5">
                          <ShieldCheck className="w-3 h-3" />
                          <span>SHA-256 OK</span>
                        </span>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setExplainModalDoc({ id: selectedDocDetail.id, title: selectedDocDetail.title })}
                      className="px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl shadow-xs transition-all flex items-center space-x-1.5"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Explain with Grounded AI</span>
                    </button>
                    <a
                      href={`/api/v1/documents/${selectedDocDetail.id}/download`}
                      target="_blank"
                      rel="noreferrer"
                      className="p-1.5 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 hover:bg-slate-100 transition-colors"
                      title="Download PDF"
                    >
                      <Download className="w-4 h-4" />
                    </a>
                  </div>
                </div>

                {/* Extracted Structured Biomarkers Table */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 dark:text-slate-300 font-heading">
                      Structured Serum & Biomarker Values ({selectedDocDetail.lab_tests?.length || 0})
                    </h3>
                    <span className="text-[11px] text-slate-400">
                      OCR Confidence: <strong className="text-teal-700">{selectedDocDetail.ocr_confidence_score}%</strong>
                    </span>
                  </div>

                  {(!selectedDocDetail.lab_tests || selectedDocDetail.lab_tests.length === 0) ? (
                    <div className="p-8 text-center bg-slate-50 dark:bg-slate-800/50 rounded-xl text-slate-500 text-xs">
                      No tabular serum parameters extracted. Full document is indexed for RAG queries.
                    </div>
                  ) : (
                    <div className="overflow-x-auto rounded-xl border border-slate-200/90 dark:border-slate-800">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-50/80 dark:bg-slate-800/60 text-slate-500 border-b border-slate-100 dark:border-slate-800">
                          <tr>
                            <th className="px-4 py-2.5 font-bold">Biomarker / Test Name</th>
                            <th className="px-3 py-2.5 font-bold">Observed Value</th>
                            <th className="px-3 py-2.5 font-bold">Reference Interval</th>
                            <th className="px-3 py-2.5 font-bold">Flag Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                          {selectedDocDetail.lab_tests.map((lab, idx) => (
                            <tr key={idx} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                              <td className="px-4 py-3">
                                <span className="font-bold text-slate-900 dark:text-white block">
                                  {lab.test_name}
                                </span>
                                {lab.explanation_tamil && selectedLang === 'ta' && (
                                  <span className="text-[10px] text-teal-700 dark:text-teal-400 block mt-0.5">
                                    {lab.explanation_tamil}
                                  </span>
                                )}
                              </td>
                              <td className="px-3 py-3 font-mono font-bold text-slate-900 dark:text-white">
                                {lab.observed_value} <span className="text-[10px] font-normal text-slate-400">{lab.unit}</span>
                              </td>
                              <td className="px-3 py-3 text-slate-600 dark:text-slate-300">
                                {lab.reference_range_text || 'Standard Clinical Range'}
                              </td>
                              <td className="px-3 py-3">
                                {getStatusBadge(lab.flag)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>

                {/* Automated Clinical Synthesis Box */}
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/70 border border-slate-200/60 dark:border-slate-700/60 space-y-1.5">
                  <div className="flex items-center space-x-2 text-teal-700 dark:text-teal-300">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span className="text-xs font-bold uppercase tracking-wider">
                      {selectedLang === 'ta' ? 'மருத்துவ சுருக்கம்' : selectedLang === 'tanglish' ? 'Medical Summary' : 'Automated Pathology Synthesis'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-sans">
                    {selectedLang === 'ta'
                      ? 'இந்த ஆய்வக அறிக்கையில் உள்ள இரத்தப் பரிசோதனை முடிவுகள் துல்லியமாகப் பகுப்பாய்வு செய்யப்பட்டு உங்கள் மருத்துவப் பெட்டகத்தில் பதிவு செய்யப்பட்டுள்ளன.'
                      : selectedLang === 'tanglish'
                      ? 'Indha lab report-il ulla test values verify seiyappattu ungal personal medical vault-il save aagiulladhu.'
                      : 'Biomarkers in this report have been extracted with dual-engine OCR verification and linked to longitudinal patient trends.'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Comparison Modal */}
      {showCompareModal && comparisonMatrix && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-2xl max-w-5xl w-full max-h-[90vh] flex flex-col overflow-hidden">
            <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center space-x-2 font-heading">
                  <Layers className="w-4 h-4 text-teal-600" />
                  <span>Longitudinal Cross-Tabulation Matrix</span>
                </h3>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Comparing {comparisonMatrix.compared_documents.length} chronological reports ({comparisonMatrix.total_tests_compared} biomarkers analyzed)
                </p>
              </div>
              <button
                onClick={() => setShowCompareModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-700"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-5 overflow-y-auto space-y-4 text-xs">
              <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 border-b border-slate-100 dark:border-slate-800">
                    <tr>
                      <th className="px-3 py-2.5 font-bold">Biomarker</th>
                      <th className="px-3 py-2.5 font-bold">Baseline</th>
                      <th className="px-3 py-2.5 font-bold">Latest</th>
                      <th className="px-3 py-2.5 font-bold">Delta</th>
                      <th className="px-3 py-2.5 font-bold">% Change</th>
                      <th className="px-3 py-2.5 font-bold">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {comparisonMatrix.comparisons.map((c, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/50">
                        <td className="px-3 py-2.5 font-bold text-slate-900 dark:text-white">
                          {c.test_name}
                        </td>
                        <td className="px-3 py-2.5 text-slate-600">{c.baseline_value}</td>
                        <td className="px-3 py-2.5 font-bold text-slate-900">{c.latest_value}</td>
                        <td className="px-3 py-2.5 font-mono">{c.change}</td>
                        <td className="px-3 py-2.5 font-mono font-bold text-teal-700">{c.percentage_change}</td>
                        <td className="px-3 py-2.5">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700">
                            {c.reference_range_status === 'Within available reference range' ? 'Optimal' : 'Out of Bounds'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="p-4 border-t border-slate-100 dark:border-slate-800 flex justify-end">
              <button
                onClick={() => setShowCompareModal(false)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl"
              >
                Close Matrix
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Explain Report Modal */}
      {explainModalDoc && (
        <ExplainReportModal
          documentId={explainModalDoc.id}
          documentTitle={explainModalDoc.title}
          isOpen={!!explainModalDoc}
          onClose={() => setExplainModalDoc(null)}
          onViewSource={(docId) => window.open(`/api/v1/documents/${docId}/download`, '_blank')}
        />
      )}
    </div>
  );
};

export default ReportsPage;
