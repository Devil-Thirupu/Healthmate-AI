import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../services/api';
import ReportViewer from '../components/common/ReportViewer';
import {
  Activity,
  Lock,
  FileText,
  FlaskConical,
  Pill,
  Download,
  AlertCircle,
  CheckCircle2,
  Calendar,
  User,
  ShieldCheck,
  Loader2,
  Eye
} from 'lucide-react';

const PublicShareViewPage = () => {
  const { token } = useParams();
  const [meta, setMeta] = useState(null);
  const [pin, setPin] = useState('');
  const [records, setRecords] = useState(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isUnlocking, setIsUnlocking] = useState(false);
  const [viewingDoc, setViewingDoc] = useState(null);

  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        setIsLoading(true);
        const res = await api.get(`/sharing/public/${token}`);
        setMeta(res.data);
        // If not pin protected, attempt immediate access
        if (res.data.is_valid && !res.data.is_pin_required) {
          accessRecords('');
        }
      } catch (err) {
        setError('Invalid or expired share link');
      } finally {
        setIsLoading(false);
      }
    };
    fetchMetadata();
  }, [token]);

  const accessRecords = async (enteredPin) => {
    setIsUnlocking(true);
    setError('');
    try {
      const res = await api.post(`/sharing/public/${token}/access`, { pin: enteredPin || pin });
      setRecords(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Incorrect PIN or share link expired.');
    } finally {
      setIsUnlocking(false);
    }
  };

  const handlePinSubmit = (e) => {
    e.preventDefault();
    accessRecords(pin);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center justify-center p-4">
        <Activity className="w-8 h-8 animate-spin text-teal-600 mb-2" />
        <p className="text-xs text-slate-500 font-medium">Verifying secure medical token...</p>
      </div>
    );
  }

  if (!meta || !meta.is_valid) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center justify-center p-4">
        <div className="max-w-md w-full p-8 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-xl text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-rose-50 dark:bg-rose-950 text-rose-600 dark:text-rose-400 flex items-center justify-center mx-auto">
            <AlertCircle className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">
            Share Link Expired or Invalid
          </h2>
          <p className="text-xs text-slate-500 leading-relaxed font-normal">
            {meta?.message || 'This medical record share link has expired, exceeded allowable view limits, or been revoked by the patient.'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col selection:bg-teal-500 selection:text-white">
      {/* Header */}
      <header className="bg-white dark:bg-slate-900 border-b border-slate-200/90 dark:border-slate-800 py-4 px-6 sticky top-0 z-30 shadow-2xs">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-xl bg-teal-600 flex items-center justify-center text-white shadow-xs">
              <Activity className="w-4 h-4 text-teal-100" />
            </div>
            <span className="font-heading font-black text-base text-slate-900 dark:text-white">
              HEALTHMATE AI <span className="text-xs text-teal-600 font-bold ml-1">Consultation Portal</span>
            </span>
          </div>

          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300 text-xs font-bold">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Patient-Authorized Share</span>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-5xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* If PIN Required and not unlocked yet */}
        {!records ? (
          <div className="max-w-md mx-auto mt-12 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 p-8 shadow-xl space-y-6 text-center">
            <div className="w-12 h-12 rounded-2xl bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-400 flex items-center justify-center mx-auto">
              <Lock className="w-6 h-6" />
            </div>

            <div>
              <h2 className="text-lg font-black text-slate-900 dark:text-white">
                PIN-Protected Medical Record
              </h2>
              <p className="text-xs text-slate-500 mt-1 font-medium">
                Shared by <strong>{meta.patient_name}</strong> for {meta.recipient_name || 'Medical Consultation'}
              </p>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs flex items-center space-x-2 text-left font-medium">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handlePinSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1 text-left">
                  Enter 4-6 Digit Security PIN
                </label>
                <input
                  type="password"
                  required
                  maxLength={6}
                  value={pin}
                  onChange={(e) => setPin(e.target.value)}
                  placeholder="••••"
                  className="w-full text-center tracking-widest text-lg px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-600 text-slate-900 dark:text-white font-mono"
                />
              </div>

              <button
                type="submit"
                disabled={isUnlocking || !pin.trim()}
                className="w-full py-2.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl shadow-xs transition-all flex items-center justify-center space-x-2 cursor-pointer"
              >
                {isUnlocking ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Verifying PIN...</span>
                  </>
                ) : (
                  <span>Unlock Medical Records</span>
                )}
              </button>
            </form>
          </div>
        ) : (
          /* Unlocked Medical Records View */
          <div className="space-y-6 animate-in fade-in duration-200 pb-10">
            {/* Patient Header Banner */}
            <div className="p-6 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-300 border border-teal-200">
                    Patient Consultation File
                  </span>
                  <span className="text-xs text-slate-400 font-medium">
                    Expires: {new Date(records.expires_at).toLocaleString()}
                  </span>
                </div>
                <h1 className="text-xl font-black text-slate-900 dark:text-white">
                  {records.patient_name}
                </h1>
                <p className="text-xs text-slate-500 font-medium">
                  Gender: {records.patient_gender || 'N/A'} • DOB: {records.patient_dob || 'N/A'} • Blood Group: <strong className="text-rose-600">{records.patient_blood_group || 'N/A'}</strong>
                </p>
              </div>

              {records.patient_allergies && (
                <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 text-xs font-medium">
                  <p className="font-bold text-rose-700 dark:text-rose-300">Known Allergies:</p>
                  <p className="text-rose-600 dark:text-rose-400 mt-0.5">{records.patient_allergies}</p>
                </div>
              )}
            </div>

            {/* Shared Documents Section */}
            <div className="space-y-4">
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Authorized Clinical Documents ({records.documents.length})
              </h2>

              <div className="space-y-4">
                {records.documents.map((doc) => (
                  <div
                    key={doc.id}
                    className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-xl bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-400 flex items-center justify-center shrink-0">
                          {doc.category === 'prescription' ? (
                            <Pill className="w-5 h-5 text-emerald-600" />
                          ) : (
                            <FlaskConical className="w-5 h-5 text-teal-600" />
                          )}
                        </div>
                        <div>
                          <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                            {doc.title}
                          </h3>
                          <p className="text-xs text-slate-400 mt-0.5 font-medium">
                            Category: {doc.category.replace('_', ' ')} • Date: {doc.document_date || 'Undated'}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => setViewingDoc(doc)}
                          className="px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl shadow-xs transition-all flex items-center space-x-1.5"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>View Document</span>
                        </button>
                        {records.allow_download && (
                          <a
                            href={`/api/v1/sharing/public/${token}/document/${doc.id}/download`}
                            target="_blank"
                            rel="noreferrer"
                            className="p-1.5 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 hover:bg-slate-100 transition-colors"
                            title="Download Document"
                          >
                            <Download className="w-4 h-4" />
                          </a>
                        )}
                      </div>
                    </div>

                    {/* Prescriptions Details if present */}
                    {doc.prescriptions && doc.prescriptions.length > 0 && (
                      <div className="space-y-2 pt-3 border-t border-slate-100 dark:border-slate-800">
                        <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300">
                          Prescribed Medications
                        </h4>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {doc.prescriptions.map((p, idx) => (
                            <div key={idx} className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 text-xs border border-slate-100 dark:border-slate-800">
                              <p className="font-bold text-slate-900 dark:text-white">{p.medication_name}</p>
                              <p className="text-slate-500 mt-0.5 font-medium">{p.dosage} • {p.frequency} • {p.timing_instructions}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Lab Tests Details if present */}
                    {doc.lab_tests && doc.lab_tests.length > 0 && (
                      <div className="space-y-2 pt-3 border-t border-slate-100 dark:border-slate-800">
                        <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300">
                          Biomarker Results
                        </h4>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {doc.lab_tests.map((l, idx) => (
                            <div key={idx} className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 text-xs flex justify-between items-center border border-slate-100 dark:border-slate-800">
                              <div>
                                <p className="font-bold text-slate-900 dark:text-white">{l.test_name}</p>
                                <p className="text-slate-500 font-medium">{l.observed_value} {l.unit} [Ref: {l.reference_range_text || 'Standard'}]</p>
                              </div>
                              <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-md ${
                                l.flag === 'high' || l.flag === 'critical'
                                  ? 'bg-rose-50 text-rose-700 border border-rose-200'
                                  : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              }`}>
                                {l.flag}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Report Viewer for Public Share */}
        {viewingDoc && (
          <ReportViewer
            isOpen={!!viewingDoc}
            onClose={() => setViewingDoc(null)}
            title={viewingDoc.title}
            mimeType={viewingDoc.mime_type}
            previewUrl={`/api/v1/sharing/public/${token}/document/${viewingDoc.id}/preview`}
            downloadUrl={records?.allow_download ? `/api/v1/sharing/public/${token}/document/${viewingDoc.id}/download` : null}
            allowDownload={!!records?.allow_download}
            docData={viewingDoc}
          />
        )}
      </main>
    </div>
  );
};

export default PublicShareViewPage;
