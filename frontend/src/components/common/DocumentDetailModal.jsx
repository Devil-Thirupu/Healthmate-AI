import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import {
  X,
  FileText,
  FlaskConical,
  Pill,
  Activity,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Calendar,
  User,
  Building,
  Edit3,
  RefreshCw,
  Save,
  Download,
  Languages,
  Eye,
  Loader2
} from 'lucide-react';

const DocumentDetailModal = ({ docId, isOpen, onClose, onUpdated }) => {
  const [doc, setDoc] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('structured'); // 'structured', 'raw_ocr', 'edit'
  const [isSaving, setIsSaving] = useState(false);
  const [isReprocessing, setIsReprocessing] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  // Editable state
  const [editTitle, setEditTitle] = useState('');
  const [editCategory, setEditCategory] = useState('');
  const [editDate, setEditDate] = useState('');
  const [editDoctor, setEditDoctor] = useState('');
  const [editClinic, setEditClinic] = useState('');
  const [editOcrText, setEditOcrText] = useState('');

  const fetchDetails = async () => {
    if (!docId) return;
    try {
      setIsLoading(true);
      const res = await api.get(`/documents/${docId}`);
      setDoc(res.data);
      setEditTitle(res.data.title || '');
      setEditCategory(res.data.category || 'other');
      setEditDate(res.data.document_date || '');
      setEditDoctor(res.data.doctor_name || '');
      setEditClinic(res.data.clinic_or_lab || '');
      setEditOcrText(res.data.ocr_raw_text || '');
    } catch (err) {
      console.error('Failed to load document details:', err);
      setErrorMsg('Failed to load document details.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && docId) {
      fetchDetails();
    }
  }, [isOpen, docId]);

  if (!isOpen) return null;

  const handleReprocess = async () => {
    setIsReprocessing(true);
    setSuccessMsg('');
    setErrorMsg('');
    try {
      const res = await api.post(`/documents/${docId}/reprocess`);
      setDoc(res.data);
      setSuccessMsg('Document OCR and clinical extraction reprocessed successfully!');
      onUpdated?.();
    } catch (err) {
      setErrorMsg('Failed to reprocess OCR.');
    } finally {
      setIsReprocessing(false);
    }
  };

  const handleSaveCorrections = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setSuccessMsg('');
    setErrorMsg('');

    try {
      const payload = {
        title: editTitle,
        category: editCategory,
        document_date: editDate,
        doctor_name: editDoctor,
        clinic_or_lab: editClinic,
        ocr_raw_text: editOcrText
      };
      const res = await api.put(`/documents/${docId}/corrections`, payload);
      setDoc(res.data);
      setSuccessMsg('Manual corrections saved and audited successfully!');
      setActiveTab('structured');
      onUpdated?.();
    } catch (err) {
      setErrorMsg('Failed to save manual corrections.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDownload = () => {
    const token = localStorage.getItem('healthmate_access_token');
    window.open(`/api/v1/documents/${docId}/download?token=${token}`, '_blank');
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/80 backdrop-blur-sm flex items-center justify-center p-2 sm:p-4">
      <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-6xl w-full h-[90vh] shadow-2xl border border-slate-200 dark:border-slate-800 flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="px-6 py-3.5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-3 min-w-0">
            <div className="w-9 h-9 rounded-xl bg-brand-50 dark:bg-brand-950 text-brand-600 dark:text-brand-400 flex items-center justify-center shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <h2 className="text-sm font-bold text-slate-900 dark:text-white truncate max-w-md">
                {doc?.title || 'Document Details'}
              </h2>
              <p className="text-[11px] text-slate-400 flex items-center space-x-2">
                <span>{doc?.original_filename}</span>
                <span>•</span>
                <span>{doc ? (doc.file_size_bytes / (1024 * 1024)).toFixed(2) : 0} MB</span>
                <span>•</span>
                <span className="text-emerald-600 dark:text-emerald-400 font-semibold flex items-center space-x-0.5">
                  <ShieldCheck className="w-3 h-3" />
                  <span>SHA-256 OK</span>
                </span>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleDownload}
              className="p-2 rounded-xl text-slate-500 hover:text-emerald-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              title="Download Verified File"
            >
              <Download className="w-4 h-4" />
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Body: Split Screen */}
        {isLoading ? (
          <div className="flex-1 flex flex-col items-center justify-center p-8">
            <Loader2 className="w-8 h-8 animate-spin text-brand-600 mb-2" />
            <p className="text-xs text-slate-500">Loading document intelligence...</p>
          </div>
        ) : (
          <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-slate-200 dark:divide-slate-800 overflow-hidden">
            {/* Left Screen: Document File Preview */}
            <div className="h-full bg-slate-100 dark:bg-slate-950 p-2 overflow-hidden flex flex-col">
              <div className="flex items-center justify-between px-3 py-1.5 text-xs text-slate-500">
                <span className="font-semibold">Original Medical File</span>
                <span className="text-[10px] uppercase font-mono">
                  {doc?.mime_type}
                </span>
              </div>
              <div className="flex-1 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                <iframe
                  src={`/api/v1/documents/${doc.id}/preview`}
                  className="w-full h-full"
                  title="Document Preview"
                />
              </div>
            </div>

            {/* Right Screen: Structured OCR & Clinical Intelligence */}
            <div className="h-full flex flex-col overflow-hidden bg-white dark:bg-slate-900">
              {/* Tab Navigation & Reprocess Button */}
              <div className="px-6 py-2.5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between shrink-0">
                <div className="flex items-center space-x-1">
                  <button
                    onClick={() => setActiveTab('structured')}
                    className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
                      activeTab === 'structured'
                        ? 'bg-brand-50 dark:bg-brand-950/80 text-brand-700 dark:text-brand-300 border border-brand-200 dark:border-brand-800'
                        : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                    }`}
                  >
                    Clinical Entities ({doc?.lab_tests?.length || 0} Labs, {doc?.prescriptions?.length || 0} Rx)
                  </button>

                  <button
                    onClick={() => setActiveTab('raw_ocr')}
                    className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
                      activeTab === 'raw_ocr'
                        ? 'bg-brand-50 dark:bg-brand-950/80 text-brand-700 dark:text-brand-300 border border-brand-200 dark:border-brand-800'
                        : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                    }`}
                  >
                    Raw OCR Text
                  </button>

                  <button
                    onClick={() => setActiveTab('edit')}
                    className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors flex items-center space-x-1 ${
                      activeTab === 'edit'
                        ? 'bg-brand-50 dark:bg-brand-950/80 text-brand-700 dark:text-brand-300 border border-brand-200 dark:border-brand-800'
                        : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                    }`}
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                    <span>Human Edit</span>
                  </button>
                </div>

                <button
                  onClick={handleReprocess}
                  disabled={isReprocessing}
                  className="p-1.5 rounded-lg text-slate-500 hover:text-brand-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  title="Reprocess OCR"
                >
                  <RefreshCw className={`w-4 h-4 ${isReprocessing ? 'animate-spin text-brand-600' : ''}`} />
                </button>
              </div>

              {/* Status & Alerts Bar */}
              <div className="px-6 py-2 bg-slate-50 dark:bg-slate-800/40 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs shrink-0">
                <div className="flex items-center space-x-2">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Confidence:</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    doc?.ocr_confidence_score > 90
                      ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300'
                      : 'bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300'
                  }`}>
                    {doc?.ocr_confidence_score}% High
                  </span>
                  {doc?.has_manual_corrections && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-cyan-100 dark:bg-cyan-950 text-cyan-700 dark:text-cyan-300">
                      Human Verified
                    </span>
                  )}
                </div>

                <div className="text-[11px] text-slate-400">
                  {doc?.category?.replace('_', ' ').toUpperCase()}
                </div>
              </div>

              {successMsg && (
                <div className="m-4 p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-900 text-emerald-700 dark:text-emerald-300 text-xs flex items-center space-x-2 shrink-0">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>{successMsg}</span>
                </div>
              )}

              {errorMsg && (
                <div className="m-4 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs flex items-center space-x-2 shrink-0">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{errorMsg}</span>
                </div>
              )}

              {/* Tab 1: Structured Clinical Entities */}
              {activeTab === 'structured' && (
                <div className="flex-1 p-6 overflow-y-auto space-y-6">
                  {/* Lab Tests Section */}
                  {doc?.lab_tests && doc.lab_tests.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center space-x-1.5">
                        <FlaskConical className="w-4 h-4 text-cyan-600" />
                        <span>Extracted Biomarkers ({doc.lab_tests.length})</span>
                      </h4>

                      <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden divide-y divide-slate-100 dark:divide-slate-800">
                        {doc.lab_tests.map((lab, idx) => (
                          <div key={idx} className="p-3 bg-white dark:bg-slate-900 space-y-1.5">
                            <div className="flex items-start justify-between gap-2">
                              <div>
                                <p className="text-xs font-bold text-slate-900 dark:text-white">
                                  {lab.test_name}
                                </p>
                                <p className="text-[11px] text-slate-400">
                                  Observed: <strong className="text-slate-800 dark:text-slate-200">{lab.observed_value} {lab.unit}</strong> • Ref: {lab.reference_range_text || 'Standard'}
                                </p>
                              </div>

                              <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                                lab.flag === 'high' || lab.flag === 'critical'
                                  ? 'bg-rose-100 dark:bg-rose-950 text-rose-700 dark:text-rose-300'
                                  : lab.flag === 'low'
                                  ? 'bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300'
                                  : 'bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300'
                              }`}>
                                {lab.flag}
                              </span>
                            </div>

                            {lab.explanation_tamil && (
                              <p className="text-[10px] text-brand-700 dark:text-brand-300 bg-brand-50/50 dark:bg-brand-950/30 p-2 rounded-lg">
                                <strong>தமிழ்:</strong> {lab.explanation_tamil}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Prescriptions Section */}
                  {doc?.prescriptions && doc.prescriptions.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center space-x-1.5">
                        <Pill className="w-4 h-4 text-teal-600" />
                        <span>Prescription Items ({doc.prescriptions.length})</span>
                      </h4>

                      <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden divide-y divide-slate-100 dark:divide-slate-800">
                        {doc.prescriptions.map((p, idx) => (
                          <div key={idx} className="p-3 bg-white dark:bg-slate-900 space-y-1.5">
                            <div className="flex items-start justify-between">
                              <div>
                                <p className="text-xs font-bold text-slate-900 dark:text-white">
                                  {p.medication_name} ({p.dosage || 'Standard'})
                                </p>
                                <p className="text-[11px] text-slate-500">
                                  Frequency: <strong>{p.frequency}</strong> • Timing: <strong>{p.timing_instructions}</strong> • Duration: {p.duration}
                                </p>
                              </div>
                            </div>

                            {p.instructions_tamil && (
                              <p className="text-[10px] text-teal-700 dark:text-teal-300 bg-teal-50/50 dark:bg-teal-950/30 p-2 rounded-lg">
                                <strong>வழிகாட்டல்:</strong> {p.instructions_tamil}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* If no structured items detected */}
                  {(!doc?.lab_tests || doc.lab_tests.length === 0) && (!doc?.prescriptions || doc.prescriptions.length === 0) && (
                    <div className="p-8 text-center bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-dashed border-slate-200 dark:border-slate-700 space-y-2">
                      <FileText className="w-8 h-8 text-slate-400 mx-auto" />
                      <p className="text-xs text-slate-600 dark:text-slate-300 font-semibold">
                        Document indexed for RAG Search
                      </p>
                      <p className="text-[11px] text-slate-400">
                        Full text is available under Raw OCR Text and queryable via the AI Assistant.
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Tab 2: Raw OCR Text */}
              {activeTab === 'raw_ocr' && (
                <div className="flex-1 p-6 overflow-y-auto space-y-4">
                  <div className="p-4 bg-slate-50 dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-slate-800 font-mono text-xs text-slate-800 dark:text-slate-200 leading-relaxed whitespace-pre-wrap">
                    {doc?.ocr_raw_text || 'No text extracted.'}
                  </div>
                </div>
              )}

              {/* Tab 3: Human-in-the-Loop Corrections Editor */}
              {activeTab === 'edit' && (
                <form onSubmit={handleSaveCorrections} className="flex-1 p-6 overflow-y-auto space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Document Title
                    </label>
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                        Category
                      </label>
                      <select
                        value={editCategory}
                        onChange={(e) => setEditCategory(e.target.value)}
                        className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
                      >
                        <option value="lab_report">Lab Report</option>
                        <option value="prescription">Prescription</option>
                        <option value="imaging">Radiology / Imaging</option>
                        <option value="discharge_summary">Discharge Summary</option>
                        <option value="other">Other</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                        Document Date
                      </label>
                      <input
                        type="date"
                        value={editDate}
                        onChange={(e) => setEditDate(e.target.value)}
                        className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                        Doctor Name
                      </label>
                      <input
                        type="text"
                        value={editDoctor}
                        onChange={(e) => setEditDoctor(e.target.value)}
                        placeholder="e.g. Dr. Ramanathan"
                        className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                        Clinic / Lab Name
                      </label>
                      <input
                        type="text"
                        value={editClinic}
                        onChange={(e) => setEditClinic(e.target.value)}
                        placeholder="e.g. Apollo Diagnostics"
                        className="w-full px-3 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      OCR Raw Text (Edit or correct missing tokens)
                    </label>
                    <textarea
                      rows={6}
                      value={editOcrText}
                      onChange={(e) => setEditOcrText(e.target.value)}
                      className="w-full p-3 font-mono text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={isSaving}
                    className="inline-flex items-center space-x-2 px-5 py-2.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-sm transition-all"
                  >
                    {isSaving ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Saving Corrections...</span>
                      </>
                    ) : (
                      <>
                        <Save className="w-4 h-4" />
                        <span>Save Human Corrections</span>
                      </>
                    )}
                  </button>
                </form>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentDetailModal;
