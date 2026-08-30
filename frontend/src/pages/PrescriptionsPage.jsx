import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import api from '../services/api';
import {
  Pill,
  PlusCircle,
  Calendar,
  User,
  Clock,
  AlertTriangle,
  Languages,
  CheckCircle2,
  FileText,
  Loader2,
  Edit3,
  Check,
  History,
  ChevronDown,
  ChevronUp,
  Info,
  X
} from 'lucide-react';

const PrescriptionsPage = () => {
  const { openUpload } = useOutletContext();
  const [rxDocs, setRxDocs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedLang, setSelectedLang] = useState('en');
  const [extractionsMap, setExtractionsMap] = useState({});
  const [expandedDocId, setExpandedDocId] = useState(null);
  const [historyModalDoc, setHistoryModalDoc] = useState(null);
  const [historyList, setHistoryList] = useState([]);
  const [editModalItem, setEditModalItem] = useState(null); // { docId, extractionId, itemIndex, item }
  const [savingEdit, setSavingEdit] = useState(false);

  const fetchPrescriptions = async () => {
    try {
      setIsLoading(true);
      const res = await api.get('/documents/', { params: { category: 'prescription' } });
      const docs = res.data || [];
      setRxDocs(docs);

      // Load extractions for all fetched prescription documents
      for (const d of docs) {
        loadExtractions(d.id);
      }
    } catch (err) {
      console.error('Failed to load prescriptions:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadExtractions = async (docId) => {
    try {
      const res = await api.get(`/documents/${docId}/extractions`);
      setExtractionsMap(prev => ({
        ...prev,
        [docId]: res.data || []
      }));
    } catch (err) {
      console.error(`Failed to load extractions for doc ${docId}:`, err);
    }
  };

  useEffect(() => {
    fetchPrescriptions();
    const handleRefresh = () => fetchPrescriptions();
    window.addEventListener('healthmate_doc_uploaded', handleRefresh);
    return () => window.removeEventListener('healthmate_doc_uploaded', handleRefresh);
  }, []);


  const handleOpenHistory = async (docId) => {
    try {
      const res = await api.get(`/documents/${docId}/corrections/history`);
      setHistoryList(res.data || []);
      setHistoryModalDoc(docId);
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  };

  const handleSaveCorrection = async (e) => {
    e.preventDefault();
    if (!editModalItem) return;

    try {
      setSavingEdit(true);
      const { docId, extractionId, itemIndex, item, formValues } = editModalItem;

      // Check fields and record corrections for modified values
      const fields = ['drug_name', 'dosage', 'frequency', 'duration', 'instructions'];
      for (const field of fields) {
        if (formValues[field] !== item[field]) {
          await api.post(`/documents/${docId}/corrections/field`, {
            field_name: field,
            item_index: itemIndex,
            original_value: item[field],
            corrected_value: formValues[field],
            notes: 'User manual correction'
          }, {
            params: { extraction_id: extractionId }
          });
        }
      }

      await loadExtractions(docId);
      setEditModalItem(null);
    } catch (err) {
      console.error('Failed to save correction:', err);
      alert('Failed to save edit: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSavingEdit(false);
    }
  };

  const handleConfirmReview = async (docId, extractionId, medications) => {
    try {
      await api.post(`/documents/${docId}/confirm-review`, {
        medications: medications,
        notes: 'Confirmed by user'
      }, {
        params: { extraction_id: extractionId }
      });
      await loadExtractions(docId);
      await fetchPrescriptions();
      alert('Prescription review confirmed and schedule synchronized!');
    } catch (err) {
      console.error('Failed to confirm review:', err);
      alert('Confirmation failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const getConfidenceBadge = (level) => {
    switch (level) {
      case 'HIGH':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">HIGH</span>;
      case 'MEDIUM':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">MEDIUM</span>;
      case 'LOW':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300">LOW</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400">NOT AVAILABLE</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white font-heading">
            Prescriptions & Medication Schedule
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Prescription OCR models, structured field extraction, and trilingual medication guidance
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
            <span>Upload Prescription</span>
          </button>
        </div>
      </div>

      {/* Safety Notice */}
      <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 flex items-start space-x-3">
        <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <h4 className="text-xs font-bold text-amber-800 dark:text-amber-300">
            Prescription Integrity & User Review Policy
          </h4>
          <p className="text-xs text-amber-700 dark:text-amber-400/90 leading-relaxed">
            HealthMate AI extracts prescription content verbatim. AI models do not diagnose or modify doses. Please review extracted fields below and edit or confirm before relying on medication reminders.
          </p>
        </div>
      </div>

      {/* Prescription Documents Listing */}
      {isLoading ? (
        <div className="p-16 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
          <Loader2 className="w-7 h-7 animate-spin text-brand-600 mx-auto mb-2" />
          <p className="text-xs text-slate-500">Retrieving prescription files...</p>
        </div>
      ) : rxDocs.length === 0 ? (
        <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 space-y-3">
          <Pill className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto" />
          <div>
            <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
              No prescriptions uploaded yet
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Upload a doctor's Rx or discharge medication chart to extract medication intake instructions.
            </p>
          </div>
          <button
            onClick={openUpload}
            className="inline-flex items-center space-x-1.5 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold rounded-xl transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Upload Prescription</span>
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {rxDocs.map((doc) => {
            const extractions = extractionsMap[doc.id] || [];
            const isExpanded = expandedDocId === doc.id;

            return (
              <div
                key={doc.id}
                className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4"
              >
                {/* Top Summary Bar */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-xl bg-teal-50 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center shrink-0">
                      <Pill className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                          {doc.title}
                        </h3>
                        {extractions.some(e => e.is_user_reviewed) && (
                          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>User Reviewed</span>
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-400 flex items-center space-x-2 mt-0.5">
                        <span>Date: {doc.document_date || 'Undated'}</span>
                        {doc.doctor_name && <span>• Dr: {doc.doctor_name}</span>}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleOpenHistory(doc.id)}
                      className="px-3 py-1.5 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 transition-colors inline-flex items-center space-x-1.5"
                    >
                      <History className="w-3.5 h-3.5 text-slate-500" />
                      <span>History</span>
                    </button>

                    <a
                      href={`/api/v1/documents/${doc.id}/download`}
                      target="_blank"
                      rel="noreferrer"
                      className="px-3 py-1.5 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 transition-colors"
                    >
                      View Original Rx
                    </a>

                    <button
                      onClick={() => setExpandedDocId(isExpanded ? null : doc.id)}
                      className="px-3 py-1.5 text-xs font-bold text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-950/60 hover:bg-brand-100 dark:hover:bg-brand-900/60 rounded-xl border border-brand-200 dark:border-brand-800 transition-colors inline-flex items-center space-x-1"
                    >
                      <span>{isExpanded ? 'Hide Extractions' : 'Structured OCR Review'}</span>
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Multilingual Medication Schedule Preview */}
                <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 text-xs text-slate-600 dark:text-slate-300 space-y-1">
                  <p className="font-semibold text-slate-800 dark:text-slate-200">
                    {selectedLang === 'ta'
                      ? 'மருந்து உட்கொள்ளும் வழிகாட்டல்:'
                      : selectedLang === 'tanglish'
                      ? 'Marundhu Eduthukkollum Vazhikaattal:'
                      : 'Medication Intake Guidance:'}
                  </p>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">
                    {selectedLang === 'ta'
                      ? 'மருத்துவர் பரிந்துரைத்த சரியான அளவு மற்றும் நேரத்தில் மருந்துகளை தவறாமல் உட்கொள்ளவும். உணவுக்கு முன் (AC) அல்லது உணவுக்குப் பின் (PC) என்பதைக் கவனிக்கவும்.'
                      : selectedLang === 'tanglish'
                      ? 'Doctor sonna correct time-la marundhu saapidavum. Food saapiduvadharkku munnadi (AC) or pinnaadi (PC) enbadhai kavanikkavum.'
                      : 'Take prescribed medicines strictly as scheduled. Observe food timing rules (AC: Before meals, PC: After meals).'}
                  </p>
                </div>

                {/* Expanded Structured Extraction Drawer */}
                {isExpanded && (
                  <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-800 space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                          Structured Prescription Extractions
                        </h4>
                        <p className="text-[11px] text-slate-500">
                          Review OCR-extracted fields, correct any errors, then confirm for your medication schedule.
                        </p>
                      </div>

                      <div className="flex items-center space-x-2">
                        {/* Re-process button — runs lightweight baseline OCR extractor */}
                      </div>
                    </div>

                    {extractions.length === 0 ? (
                      <div className="p-6 text-center bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200 dark:border-slate-800">
                        <p className="text-xs text-slate-500">No extractions recorded yet for this document.</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {extractions.map((ext) => (
                          <div
                            key={ext.id}
                            className="p-4 rounded-xl bg-slate-50/70 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-3"
                          >
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                              <div className="flex items-center space-x-2.5">
                                <span className="px-2.5 py-1 rounded-lg text-xs font-bold bg-brand-100 text-brand-800 dark:bg-brand-950 dark:text-brand-300">
                                  {ext.model_name} ({ext.provider})
                                </span>
                                <div className="flex items-center space-x-1.5 text-xs text-slate-500">
                                  <span>Confidence:</span>
                                  {getConfidenceBadge(ext.confidence_level)}
                                </div>
                              </div>

                              <div className="flex items-center space-x-2">
                                {ext.is_user_reviewed ? (
                                  <span className="px-2.5 py-1 text-[11px] font-semibold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 rounded-lg flex items-center space-x-1">
                                    <Check className="w-3.5 h-3.5" />
                                    <span>User Reviewed</span>
                                  </span>
                                ) : (
                                  <button
                                    onClick={() => handleConfirmReview(doc.id, ext.id, ext.medications_json)}
                                    className="px-3 py-1 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg transition-all shadow-sm inline-flex items-center space-x-1"
                                  >
                                    <Check className="w-3.5 h-3.5" />
                                    <span>Confirm Review</span>
                                  </button>
                                )}
                              </div>
                            </div>

                            {/* Header Metadata */}
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-800">
                              <div>
                                <span className="text-[10px] uppercase font-semibold text-slate-400">Doctor</span>
                                <p className="font-medium text-slate-800 dark:text-slate-200">{ext.doctor_name}</p>
                              </div>
                              <div>
                                <span className="text-[10px] uppercase font-semibold text-slate-400">Clinic</span>
                                <p className="font-medium text-slate-800 dark:text-slate-200">{ext.clinic_name}</p>
                              </div>
                              <div>
                                <span className="text-[10px] uppercase font-semibold text-slate-400">Patient</span>
                                <p className="font-medium text-slate-800 dark:text-slate-200">{ext.patient_name}</p>
                              </div>
                              <div>
                                <span className="text-[10px] uppercase font-semibold text-slate-400">Date</span>
                                <p className="font-medium text-slate-800 dark:text-slate-200">{ext.prescription_date}</p>
                              </div>
                            </div>

                            {/* Medications Table */}
                            <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
                              <table className="w-full text-left text-xs">
                                <thead className="bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-400 font-semibold border-b border-slate-200 dark:border-slate-800">
                                  <tr>
                                    <th className="p-2.5">Medicine Name</th>
                                    <th className="p-2.5">Dosage</th>
                                    <th className="p-2.5">Frequency</th>
                                    <th className="p-2.5">Duration</th>
                                    <th className="p-2.5">Instructions</th>
                                    <th className="p-2.5 text-right">Actions</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-200 dark:divide-slate-800 bg-white dark:bg-slate-950">
                                  {ext.medications_json && ext.medications_json.length > 0 ? (
                                    ext.medications_json.map((med, idx) => (
                                      <tr key={idx} className="hover:bg-slate-50/60 dark:hover:bg-slate-900/60">
                                        <td className="p-2.5 font-bold text-slate-900 dark:text-white">
                                          <div>{med.drug_name}</div>
                                          {med.normalized_name && med.normalized_name !== 'Not available in source' && med.normalized_name !== med.drug_name && (
                                            <span className="text-[10px] font-normal text-teal-600 dark:text-teal-400">
                                              Normalized: {med.normalized_name}
                                            </span>
                                          )}
                                        </td>
                                        <td className="p-2.5 text-slate-700 dark:text-slate-300">{med.dosage}</td>
                                        <td className="p-2.5 text-slate-700 dark:text-slate-300">{med.frequency}</td>
                                        <td className="p-2.5 text-slate-700 dark:text-slate-300">{med.duration}</td>
                                        <td className="p-2.5 text-slate-700 dark:text-slate-300">{med.instructions}</td>
                                        <td className="p-2.5 text-right">
                                          <button
                                            onClick={() => setEditModalItem({
                                              docId: doc.id,
                                              extractionId: ext.id,
                                              itemIndex: idx,
                                              item: med,
                                              formValues: { ...med }
                                            })}
                                            className="px-2 py-1 text-[11px] font-semibold text-brand-600 dark:text-brand-400 hover:bg-brand-50 dark:hover:bg-brand-950 rounded-lg transition-colors inline-flex items-center space-x-1"
                                          >
                                            <Edit3 className="w-3 h-3" />
                                            <span>Edit</span>
                                          </button>
                                        </td>
                                      </tr>
                                    ))
                                  ) : (
                                    <tr>
                                      <td colSpan="6" className="p-4 text-center text-slate-400">
                                        No medication records parsed. Output marked for manual review.
                                      </td>
                                    </tr>
                                  )}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Edit Medication Modal */}
      {editModalItem && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 max-w-lg w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center space-x-2">
                <Edit3 className="w-4 h-4 text-brand-600" />
                <span>Manual Prescription Field Edit</span>
              </h3>
              <button
                onClick={() => setEditModalItem(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveCorrection} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Medicine / Drug Name</label>
                <input
                  type="text"
                  required
                  value={editModalItem.formValues.drug_name || ''}
                  onChange={(e) => setEditModalItem({
                    ...editModalItem,
                    formValues: { ...editModalItem.formValues, drug_name: e.target.value }
                  })}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Dosage</label>
                  <input
                    type="text"
                    value={editModalItem.formValues.dosage || ''}
                    onChange={(e) => setEditModalItem({
                      ...editModalItem,
                      formValues: { ...editModalItem.formValues, dosage: e.target.value }
                    })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Frequency</label>
                  <input
                    type="text"
                    value={editModalItem.formValues.frequency || ''}
                    onChange={(e) => setEditModalItem({
                      ...editModalItem,
                      formValues: { ...editModalItem.formValues, frequency: e.target.value }
                    })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Duration</label>
                  <input
                    type="text"
                    value={editModalItem.formValues.duration || ''}
                    onChange={(e) => setEditModalItem({
                      ...editModalItem,
                      formValues: { ...editModalItem.formValues, duration: e.target.value }
                    })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Instructions</label>
                  <input
                    type="text"
                    value={editModalItem.formValues.instructions || ''}
                    onChange={(e) => setEditModalItem({
                      ...editModalItem,
                      formValues: { ...editModalItem.formValues, instructions: e.target.value }
                    })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div className="pt-3 flex items-center justify-end space-x-2 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setEditModalItem(null)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingEdit}
                  className="px-4 py-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-xs font-semibold rounded-xl shadow-md"
                >
                  {savingEdit ? 'Saving...' : 'Save Correction'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Provenance Edit History Modal */}
      {historyModalDoc && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 max-w-xl w-full p-6 space-y-4 shadow-xl max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center space-x-2">
                <History className="w-4 h-4 text-brand-600" />
                <span>Field Correction Audit History</span>
              </h3>
              <button
                onClick={() => setHistoryModalDoc(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2.5">
              {historyList.length === 0 ? (
                <div className="p-8 text-center text-slate-400 text-xs">
                  No manual edits recorded for this prescription document yet.
                </div>
              ) : (
                historyList.map((hist) => (
                  <div
                    key={hist.id}
                    className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-brand-700 dark:text-brand-400 uppercase text-[10px]">
                        Field: {hist.field_name} (Item #{hist.item_index + 1})
                      </span>
                      <span className="text-[10px] text-slate-400">
                        {new Date(hist.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                      <div className="p-2 rounded bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300">
                        <span className="block text-[9px] font-bold text-red-500 uppercase">Original AI Extracted</span>
                        {hist.original_value || 'None'}
                      </div>
                      <div className="p-2 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300">
                        <span className="block text-[9px] font-bold text-emerald-500 uppercase">User Corrected</span>
                        {hist.corrected_value}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="pt-3 border-t border-slate-200 dark:border-slate-800 text-right">
              <button
                onClick={() => setHistoryModalDoc(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-semibold rounded-xl"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PrescriptionsPage;
