import React, { useState, useEffect, useRef } from 'react';
import { useOutletContext } from 'react-router-dom';
import api from '../services/api';
import ReportViewer from '../components/common/ReportViewer';
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
  X,
  RefreshCw,
  ShieldCheck,
  Building,
  Camera,
  UploadCloud,
  Eye,
  Bell,
  BellOff,
  BellRing,
  ArrowRight
} from 'lucide-react';
import MedicationScheduleCard from '../components/common/MedicationScheduleCard';

const PrescriptionsPage = () => {
  const { openUpload } = useOutletContext();
  const [rxDocs, setRxDocs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedLang, setSelectedLang] = useState('en');
  const [extractionsMap, setExtractionsMap] = useState({});
  const [expandedDocId, setExpandedDocId] = useState(null);
  const [historyModalDoc, setHistoryModalDoc] = useState(null);
  const [historyList, setHistoryList] = useState([]);
  const [editModalItem, setEditModalItem] = useState(null);
  const [savingEdit, setSavingEdit] = useState(false);

  // Stepped Review Modal state (ONE medicine at a time)
  const [steppedReview, setSteppedReview] = useState(null); // { docId, extractionId, medications: [], currentIndex: 0, confirmedMeds: [] }
  const [cameraFile, setCameraFile] = useState(null);
  const [viewingDoc, setViewingDoc] = useState(null);
  const [notifStatus, setNotifStatus] = useState('Checking...');
  const cameraInputRef = useRef(null);

  useEffect(() => {
    if (!('Notification' in window)) {
      setNotifStatus('Not supported');
    } else if (Notification.permission === 'granted') {
      setNotifStatus('Enabled');
    } else if (Notification.permission === 'denied') {
      setNotifStatus('Blocked');
    } else {
      setNotifStatus('Click to Enable');
    }
  }, []);

  const requestNotificationPermission = async () => {
    if (!('Notification' in window)) return;
    try {
      const res = await Notification.requestPermission();
      if (res === 'granted') setNotifStatus('Enabled');
      else if (res === 'denied') setNotifStatus('Blocked');
      else setNotifStatus('Click to Enable');
    } catch (e) {
      console.error('Notification error:', e);
    }
  };

  const fetchPrescriptions = async () => {
    try {
      setIsLoading(true);
      const res = await api.get('/documents/', { params: { category: 'prescription' } });
      const docs = res.data || [];
      setRxDocs(docs);

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

  const handleStartSteppedReview = (docId, extractionId, medications) => {
    setSteppedReview({
      docId,
      extractionId,
      medications: medications || [],
      currentIndex: 0,
      confirmedMeds: []
    });
  };

  const handleConfirmCurrentMed = (med) => {
    if (!steppedReview) return;
    const updatedConfirmed = [...steppedReview.confirmedMeds, med];
    const nextIndex = steppedReview.currentIndex + 1;
    if (nextIndex >= steppedReview.medications.length) {
      handleCompleteSteppedReview(steppedReview.docId, steppedReview.extractionId, updatedConfirmed);
    } else {
      setSteppedReview({
        ...steppedReview,
        currentIndex: nextIndex,
        confirmedMeds: updatedConfirmed
      });
    }
  };

  const handleSkipCurrentMed = () => {
    if (!steppedReview) return;
    const nextIndex = steppedReview.currentIndex + 1;
    if (nextIndex >= steppedReview.medications.length) {
      handleCompleteSteppedReview(steppedReview.docId, steppedReview.extractionId, steppedReview.confirmedMeds);
    } else {
      setSteppedReview({
        ...steppedReview,
        currentIndex: nextIndex
      });
    }
  };

  const handleCompleteSteppedReview = async (docId, extractionId, confirmedMeds) => {
    try {
      await api.post(`/documents/${docId}/confirm-review`, {
        medications: confirmedMeds,
        notes: 'Confirmed via Stepped Clinical Review'
      }, {
        params: { extraction_id: extractionId }
      });
      await loadExtractions(docId);
      await fetchPrescriptions();
      setSteppedReview(null);
      alert(`Prescription confirmed! ${confirmedMeds.length} medicines added to your schedule.`);
    } catch (err) {
      alert('Confirmation failed: ' + (err.response?.data?.detail || err.message));
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
        return <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200/60 dark:bg-emerald-950 dark:text-emerald-300">HIGH</span>;
      case 'MEDIUM':
        return <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200/60 dark:bg-amber-950 dark:text-amber-300">MEDIUM</span>;
      case 'LOW':
        return <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200/60 dark:bg-rose-950 dark:text-rose-300">LOW</span>;
      default:
        return <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 text-slate-600">STANDARD</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-extrabold uppercase tracking-widest text-teal-700 bg-teal-50 dark:bg-teal-950/60 px-2.5 py-0.5 rounded-full border border-teal-200/60 dark:border-teal-800/50">
              Pharmacy & Prescription Hub
            </span>
            <span className="text-xs text-slate-400">
              • Ingested Rx: <strong className="text-slate-800 dark:text-slate-200">{rxDocs.length} Records</strong>
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white font-heading tracking-tight mt-1">
            Pharmacy & Prescription Management
          </h1>
          <p className="text-xs text-slate-500 max-w-2xl mt-0.5">
            Prescription OCR extraction, structured medication registry, human review audit trail, and trilingual dosage instructions.
          </p>
        </div>

        <div className="flex items-center flex-wrap gap-2.5 shrink-0">
          {/* Notification Permission Indicator */}
          <button
            onClick={requestNotificationPermission}
            className={`inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold shadow-2xs transition-all ${
              notifStatus === 'Enabled'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-950/60 dark:border-emerald-800 dark:text-emerald-300'
                : notifStatus === 'Blocked'
                ? 'bg-rose-50 border-rose-200 text-rose-700 dark:bg-rose-950/60 dark:border-rose-800 dark:text-rose-300'
                : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50'
            }`}
            title="Browser Notification Status for Medicine Reminders"
          >
            {notifStatus === 'Enabled' ? (
              <BellRing className="w-3.5 h-3.5 text-emerald-600" />
            ) : (
              <BellOff className="w-3.5 h-3.5 text-slate-400" />
            )}
            <span>Reminders: {notifStatus}</span>
          </button>
          {/* Trilingual Switcher */}
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
              Multilanguage
            </button>
          </div>

          <button
            onClick={openUpload}
            className="inline-flex items-center space-x-1.5 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl shadow-xs transition-all active:scale-95"
          >
            <PlusCircle className="w-4 h-4" />
            <span>+ Ingest Prescription</span>
          </button>
        </div>
      </div>

      {/* Medication Schedule & Adherence Component matching medicine-reminders.png */}
      <MedicationScheduleCard onOpenPrescription={(docId) => setExpandedDocId(docId)} />

      {/* Prescription Documents Archive Listing */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900 dark:text-white font-heading">
            Prescription Registry & Review ({rxDocs.length})
          </h2>
          <span className="text-xs text-slate-400">
            Click "Structured OCR Review" to inspect drug names and frequencies
          </span>
        </div>

        {isLoading ? (
          <div className="p-16 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800">
            <Loader2 className="w-6 h-6 animate-spin text-teal-600 mx-auto mb-2" />
            <p className="text-xs text-slate-400">Retrieving prescription records...</p>
          </div>
        ) : rxDocs.length === 0 ? (
          <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-200 dark:border-slate-700 space-y-3">
            <Pill className="w-10 h-10 text-slate-300 mx-auto" />
            <div>
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200">
                No prescriptions found
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Upload a doctor's Rx or hospital discharge medication sheet to extract medicines.
              </p>
            </div>
            <button
              onClick={openUpload}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-teal-600 text-white text-xs font-bold rounded-xl shadow-xs"
            >
              <PlusCircle className="w-3.5 h-3.5" />
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
                  className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-4"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 rounded-xl bg-teal-50 dark:bg-teal-950 text-teal-600 flex items-center justify-center shrink-0">
                        <Pill className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <h3 className="text-sm font-bold text-slate-900 dark:text-white font-heading">
                            {doc.title}
                          </h3>
                          {extractions.some(e => e.is_user_reviewed) && (
                            <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200/60">
                              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                              <span>Verified</span>
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-400 flex items-center space-x-2 mt-0.5">
                          <span>Date: {doc.document_date || 'Undated'}</span>
                          {doc.doctor_name && <span>• Dr: {doc.doctor_name}</span>}
                          {doc.clinic_or_lab && <span>• {doc.clinic_or_lab}</span>}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleOpenHistory(doc.id)}
                        className="px-3 py-1.5 text-xs font-bold text-slate-600 hover:bg-slate-100 rounded-xl border border-slate-200 dark:border-slate-700 transition-colors inline-flex items-center space-x-1.5"
                      >
                        <History className="w-3.5 h-3.5 text-slate-400" />
                        <span>Audit Log</span>
                      </button>

                      <a
                        href={`/api/v1/documents/${doc.id}/download`}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl border border-slate-200 dark:border-slate-700 transition-colors"
                      >
                        Original Rx
                      </a>

                      <button
                        onClick={() => setExpandedDocId(isExpanded ? null : doc.id)}
                        className="px-3 py-1.5 text-xs font-bold text-teal-700 bg-teal-50 hover:bg-teal-100 rounded-xl border border-teal-200/80 transition-colors inline-flex items-center space-x-1"
                      >
                        <span>{isExpanded ? 'Hide Extractions' : 'Structured Review'}</span>
                        {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      </button>
                    </div>
                  </div>

                  {/* Multilingual Medication Schedule Preview */}
                  <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 text-xs text-slate-600 dark:text-slate-300 space-y-1">
                    <p className="font-bold text-slate-800 dark:text-slate-200">
                      {selectedLang === 'ta'
                        ? 'மருந்து உட்கொள்ளும் வழிகாட்டல்:'
                        : selectedLang === 'tanglish'
                        ? 'Marundhu Eduthukkollum Vazhikaattal:'
                        : 'Clinical Intake Guidance:'}
                    </p>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                      {selectedLang === 'ta'
                        ? 'மருத்துவர் பரிந்துரைத்த சரியான அளவு மற்றும் நேரத்தில் மருந்துகளை தவறாமல் உட்கொள்ளவும். உணவுக்கு முன் (AC) அல்லது உணவுக்குப் பின் (PC) என்பதைக் கவனிக்கவும்.'
                        : selectedLang === 'tanglish'
                        ? 'Doctor sonna correct time-la marundhu saapidavum. Food saapiduvadharkku munnadi (AC) or pinnaadi (PC) enbadhai kavanikkavum.'
                        : 'Take prescribed medicines strictly as scheduled. Observe food timing rules (AC: Before meals, PC: After meals).'}
                    </p>
                  </div>

                  {/* Expanded Structured Extraction Drawer */}
                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800 space-y-4">
                      <div>
                        <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider font-heading">
                          OCR Extracted Pharmacological Entities
                        </h4>
                        <p className="text-[11px] text-slate-400">
                          Review extracted medicines, make human corrections if needed, and confirm schedule.
                        </p>
                      </div>

                      {extractions.length === 0 ? (
                        <div className="p-6 text-center bg-slate-50 dark:bg-slate-800/40 rounded-xl">
                          <p className="text-xs text-slate-400">No extractions recorded yet for this document.</p>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          {extractions.map((ext) => (
                            <div
                              key={ext.id}
                              className="p-4 rounded-xl bg-slate-50/70 dark:bg-slate-800/40 border border-slate-200/90 dark:border-slate-800 space-y-3"
                            >
                              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                                <div className="flex items-center space-x-2.5">
                                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-teal-50 text-teal-800 border border-teal-200">
                                    {ext.model_name}
                                  </span>
                                  <div className="flex items-center space-x-1.5 text-xs text-slate-500">
                                    <span>OCR Confidence:</span>
                                    {getConfidenceBadge(ext.confidence_level)}
                                  </div>
                                </div>

                                <div className="flex items-center space-x-2">
                                  {ext.is_user_reviewed ? (
                                    <span className="px-2.5 py-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 rounded-lg flex items-center space-x-1 border border-emerald-200/60">
                                      <Check className="w-3.5 h-3.5" />
                                      <span>Verified</span>
                                    </span>
                                  ) : (
                                    <div className="flex items-center space-x-2">
                                      <button
                                        onClick={() => handleStartSteppedReview(doc.id, ext.id, ext.medications_json)}
                                        className="px-3 py-1.5 text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 rounded-xl transition-all shadow-xs inline-flex items-center space-x-1"
                                      >
                                        <CheckCircle2 className="w-3.5 h-3.5" />
                                        <span>Step-by-Step Review</span>
                                      </button>
                                      <button
                                        onClick={() => handleConfirmReview(doc.id, ext.id, ext.medications_json)}
                                        className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl border border-slate-200 transition-colors inline-flex items-center space-x-1"
                                        title="Instantly add all detected medicines to schedule"
                                      >
                                        <Check className="w-3.5 h-3.5 text-teal-600" />
                                        <span>Confirm All</span>
                                      </button>
                                    </div>
                                  )}
                                </div>
                              </div>

                              {/* Medications Table */}
                              <div className="overflow-x-auto rounded-xl border border-slate-200/90 dark:border-slate-800">
                                <table className="w-full text-left text-xs">
                                  <thead className="bg-slate-100/70 dark:bg-slate-900 text-slate-600 font-bold border-b border-slate-200/90 dark:border-slate-800">
                                    <tr>
                                      <th className="p-3">Medicine / Drug Name</th>
                                      <th className="p-3">Dosage</th>
                                      <th className="p-3">Frequency</th>
                                      <th className="p-3">Duration</th>
                                      <th className="p-3">Instructions</th>
                                      <th className="p-3 text-right">Action</th>
                                    </tr>
                                  </thead>
                                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800 bg-white dark:bg-slate-950">
                                    {ext.medications_json && ext.medications_json.length > 0 ? (
                                      ext.medications_json.map((med, idx) => (
                                        <tr key={idx} className="hover:bg-slate-50/60">
                                          <td className="p-3 font-bold text-slate-900 dark:text-white">
                                            <div>{med.drug_name}</div>
                                            {med.normalized_name && med.normalized_name !== 'Not available in source' && med.normalized_name !== med.drug_name && (
                                              <span className="text-[10px] font-normal text-teal-600 block mt-0.5">
                                                Normalized: {med.normalized_name}
                                              </span>
                                            )}
                                          </td>
                                          <td className="p-3 text-slate-700">{med.dosage}</td>
                                          <td className="p-3 text-slate-700">{med.frequency}</td>
                                          <td className="p-3 text-slate-700">{med.duration}</td>
                                          <td className="p-3 text-slate-700">{med.instructions}</td>
                                          <td className="p-3 text-right">
                                            <button
                                              onClick={() => setEditModalItem({
                                                docId: doc.id,
                                                extractionId: ext.id,
                                                itemIndex: idx,
                                                item: med,
                                                formValues: { ...med }
                                              })}
                                              className="px-2.5 py-1 text-[11px] font-bold text-teal-700 hover:bg-teal-50 rounded-lg transition-colors inline-flex items-center space-x-1"
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
                                          No medication items parsed from OCR stream.
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
      </div>

      {/* Edit Medication Modal */}
      {editModalItem && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 max-w-lg w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center space-x-2 font-heading">
                <Edit3 className="w-4 h-4 text-teal-600" />
                <span>Manual Prescription Field Correction</span>
              </h3>
              <button
                onClick={() => setEditModalItem(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveCorrection} className="space-y-3 text-xs">
              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Medicine / Drug Name</label>
                <input
                  type="text"
                  required
                  value={editModalItem.formValues.drug_name || ''}
                  onChange={(e) => setEditModalItem({
                    ...editModalItem,
                    formValues: { ...editModalItem.formValues, drug_name: e.target.value }
                  })}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Dosage</label>
                  <input
                    type="text"
                    value={editModalItem.formValues.dosage || ''}
                    onChange={(e) => setEditModalItem({
                      ...editModalItem,
                      formValues: { ...editModalItem.formValues, dosage: e.target.value }
                    })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Frequency</label>
                  <input
                    type="text"
                    value={editModalItem.formValues.frequency || ''}
                    onChange={(e) => setEditModalItem({
                      ...editModalItem,
                      formValues: { ...editModalItem.formValues, frequency: e.target.value }
                    })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Duration</label>
                  <input
                    type="text"
                    value={editModalItem.formValues.duration || ''}
                    onChange={(e) => setEditModalItem({
                      ...editModalItem,
                      formValues: { ...editModalItem.formValues, duration: e.target.value }
                    })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Instructions</label>
                  <input
                    type="text"
                    value={editModalItem.formValues.instructions || ''}
                    onChange={(e) => setEditModalItem({
                      ...editModalItem,
                      formValues: { ...editModalItem.formValues, instructions: e.target.value }
                    })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                  />
                </div>
              </div>

              <div className="pt-3 flex items-center justify-end space-x-2 border-t border-slate-100 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setEditModalItem(null)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingEdit}
                  className="px-4 py-2 bg-teal-600 hover:bg-teal-700 disabled:opacity-60 text-white text-xs font-bold rounded-xl shadow-xs"
                >
                  {savingEdit ? 'Saving...' : 'Save Correction'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* History Audit Modal */}
      {historyModalDoc && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 max-w-xl w-full p-6 space-y-4 shadow-xl max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center space-x-2 font-heading">
                <History className="w-4 h-4 text-teal-600" />
                <span>Prescription Field Correction Audit</span>
              </h3>
              <button
                onClick={() => setHistoryModalDoc(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
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
                    className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700 text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-teal-700 dark:text-teal-400 uppercase text-[10px]">
                        Field: {hist.field_name} (Item #{hist.item_index + 1})
                      </span>
                      <span className="text-[10px] text-slate-400">
                        {new Date(hist.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                      <div className="p-2 rounded bg-rose-50 text-rose-700">
                        <span className="block text-[9px] font-bold text-rose-500 uppercase">Original AI Extracted</span>
                        {hist.original_value || 'None'}
                      </div>
                      <div className="p-2 rounded bg-emerald-50 text-emerald-700">
                        <span className="block text-[9px] font-bold text-emerald-500 uppercase">User Corrected</span>
                        {hist.corrected_value}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="pt-3 border-t border-slate-100 dark:border-slate-800 text-right">
              <button
                onClick={() => setHistoryModalDoc(null)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl"
              >
                Close Audit
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Stepped Medicine Confirmation Modal (ONE Medicine at a Time) */}
      {steppedReview && steppedReview.medications.length > 0 && (
        <div className="fixed inset-0 z-50 bg-slate-900/70 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 max-w-lg w-full p-6 space-y-5 shadow-2xl animate-in fade-in zoom-in-95">
            {/* Step Header */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <div className="flex items-center space-x-2">
                <span className="text-[11px] font-extrabold px-2.5 py-0.5 rounded-full bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800 uppercase tracking-wider">
                  Medicine {steppedReview.currentIndex + 1} of {steppedReview.medications.length}
                </span>
                <span className="text-xs text-slate-400 font-medium">
                  Step-by-Step Clinical Verification
                </span>
              </div>
              <button
                onClick={() => setSteppedReview(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-teal-600 h-1.5 rounded-full transition-all duration-300"
                style={{
                  width: `${((steppedReview.currentIndex + 1) / steppedReview.medications.length) * 100}%`
                }}
              ></div>
            </div>

            {/* Active Medicine Card */}
            {(() => {
              const currentMed = steppedReview.medications[steppedReview.currentIndex] || {};
              return (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-slate-50/80 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700 space-y-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="text-[10px] uppercase font-bold text-slate-400">Detected Medication</span>
                        <h3 className="text-base font-bold text-slate-900 dark:text-white font-heading">
                          {currentMed.drug_name || 'Uncertain Medicine Name'}
                        </h3>
                        {currentMed.normalized_name && currentMed.normalized_name !== currentMed.drug_name && (
                          <span className="text-xs text-teal-600 font-semibold block mt-0.5">
                            Standard Catalog: {currentMed.normalized_name}
                          </span>
                        )}
                      </div>
                      <Pill className="w-6 h-6 text-teal-600 shrink-0" />
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                      <div className="p-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800">
                        <span className="text-[10px] text-slate-400 block font-bold">Dosage</span>
                        <span className="font-semibold text-slate-800 dark:text-slate-200">{currentMed.dosage || 'Not specified'}</span>
                      </div>
                      <div className="p-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800">
                        <span className="text-[10px] text-slate-400 block font-bold">Frequency</span>
                        <span className="font-semibold text-slate-800 dark:text-slate-200">{currentMed.frequency || 'OD / As directed'}</span>
                      </div>
                      <div className="p-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800">
                        <span className="text-[10px] text-slate-400 block font-bold">Duration</span>
                        <span className="font-semibold text-slate-800 dark:text-slate-200">{currentMed.duration || 'Full course'}</span>
                      </div>
                      <div className="p-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800">
                        <span className="text-[10px] text-slate-400 block font-bold">Instructions</span>
                        <span className="font-semibold text-slate-800 dark:text-slate-200">{currentMed.instructions || 'After meals (PC)'}</span>
                      </div>
                    </div>

                    {/* Low Confidence Verification Notice */}
                    <div className="p-2.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200/80 dark:border-amber-900/60 text-xs text-amber-800 dark:text-amber-200 flex items-start space-x-2">
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                      <div>
                        <p className="font-bold">Human Verification Required</p>
                        <p className="text-[11px] text-amber-700 dark:text-amber-300">
                          {currentMed.confidence_level === 'LOW'
                            ? 'Medicine name may be uncertain due to doctor handwriting. Please verify carefully.'
                            : 'Ensure this matches your physical prescription slip.'}
                        </p>
                      </div>
                    </div>

                    {/* Optional Tablet Packaging Camera/File Assistant */}
                    <div className="pt-2 border-t border-slate-200/60 dark:border-slate-700/60 flex items-center justify-between text-xs">
                      <input
                        type="file"
                        ref={cameraInputRef}
                        accept="image/*"
                        capture="environment"
                        onChange={(e) => {
                          if (e.target.files?.[0]) setCameraFile(e.target.files[0]);
                        }}
                        className="hidden"
                      />
                      <button
                        type="button"
                        onClick={() => cameraInputRef.current?.click()}
                        className="inline-flex items-center space-x-1.5 text-slate-600 hover:text-teal-600 font-semibold"
                      >
                        <Camera className="w-4 h-4 text-teal-600" />
                        <span>{cameraFile ? 'Tablet Image Attached' : 'Capture Tablet Packaging (Optional)'}</span>
                      </button>
                      <span className="text-[10px] text-slate-400">Assistance only</span>
                    </div>
                  </div>

                  {/* Actions Bar */}
                  <div className="flex items-center justify-between gap-2 pt-2">
                    <button
                      type="button"
                      onClick={handleSkipCurrentMed}
                      className="px-4 py-2 text-xs font-semibold text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/50 rounded-xl transition-colors"
                    >
                      Reject / Skip
                    </button>

                    <div className="flex items-center space-x-2">
                      <button
                        type="button"
                        onClick={() => {
                          setEditModalItem({
                            docId: steppedReview.docId,
                            extractionId: steppedReview.extractionId,
                            itemIndex: steppedReview.currentIndex,
                            item: currentMed,
                            formValues: { ...currentMed }
                          });
                        }}
                        className="px-3.5 py-2 text-xs font-bold text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 transition-colors inline-flex items-center space-x-1"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                        <span>Edit</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => handleConfirmCurrentMed(currentMed)}
                        className="px-5 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl shadow-xs transition-all inline-flex items-center space-x-1.5"
                      >
                        <Check className="w-3.5 h-3.5" />
                        <span>
                          {steppedReview.currentIndex + 1 === steppedReview.medications.length
                            ? 'Confirm & Finish'
                            : 'Confirm & Next'}
                        </span>
                      </button>
                    </div>
                  </div>
                </div>
              );
            })()}
          </div>
        </div>
      )}

      {/* Reusable Report Viewer */}
      {viewingDoc && (
        <ReportViewer
          isOpen={!!viewingDoc}
          onClose={() => setViewingDoc(null)}
          title={viewingDoc.title}
          mimeType={viewingDoc.mime_type}
          previewUrl={`/api/v1/documents/${viewingDoc.id}/preview?token=${localStorage.getItem('healthmate_access_token') || ''}`}
          downloadUrl={`/api/v1/documents/${viewingDoc.id}/download?token=${localStorage.getItem('healthmate_access_token') || ''}`}
          allowDownload={true}
          docData={viewingDoc}
        />
      )}
    </div>
  );
};

export default PrescriptionsPage;
