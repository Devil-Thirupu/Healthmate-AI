import React, { useState } from 'react';
import {
  X,
  FileText,
  FlaskConical,
  Pill,
  Download,
  ExternalLink,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Copy,
  Check,
  RefreshCw
} from 'lucide-react';

const ReportViewer = ({
  isOpen,
  onClose,
  title,
  mimeType,
  previewUrl,
  downloadUrl,
  docData = {},
  allowDownload = true,
  onRetry
}) => {
  const [activeTab, setActiveTab] = useState('original'); // 'original', 'ocr', 'structured'
  const [zoomLevel, setZoomLevel] = useState(1);
  const [copied, setCopied] = useState(false);
  const [previewError, setPreviewError] = useState(false);
  const [isLoadingPreview, setIsLoadingPreview] = useState(true);

  if (!isOpen) return null;

  const isPdf = (mimeType || '').toLowerCase().includes('pdf') || (previewUrl || '').toLowerCase().includes('.pdf');
  const isImage = (mimeType || '').toLowerCase().includes('image') || /\.(png|jpe?g|webp|gif|bmp)$/i.test(previewUrl || '');

  const handleZoomIn = () => setZoomLevel((z) => Math.min(z + 0.25, 3));
  const handleZoomOut = () => setZoomLevel((z) => Math.max(z - 0.25, 0.5));
  const handleResetZoom = () => setZoomLevel(1);

  const handleCopyOcr = () => {
    if (docData.ocr_raw_text) {
      navigator.clipboard.writeText(docData.ocr_raw_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/80 backdrop-blur-xs flex items-center justify-center p-2 sm:p-4">
      <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-6xl w-full h-[92vh] shadow-2xl border border-slate-200/90 dark:border-slate-800 flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header Bar */}
        <div className="px-6 py-3 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between shrink-0 bg-slate-50/50 dark:bg-slate-900">
          <div className="flex items-center space-x-3 min-w-0">
            <div className="w-9 h-9 rounded-xl bg-teal-50 dark:bg-teal-950 text-teal-600 flex items-center justify-center shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <h2 className="text-sm font-bold text-slate-900 dark:text-white truncate max-w-md font-heading">
                {title || docData.title || 'Medical Document Viewer'}
              </h2>
              <p className="text-[11px] text-slate-400 flex items-center space-x-2 mt-0.5">
                <span>{docData.document_date || 'Undated Record'}</span>
                {docData.clinic_or_lab && <span>• {docData.clinic_or_lab}</span>}
                {docData.doctor_name && <span>• Dr: {docData.doctor_name}</span>}
                <span className="text-emerald-600 font-bold flex items-center space-x-0.5">
                  <ShieldCheck className="w-3 h-3" />
                  <span>SHA-256 Verified</span>
                </span>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* View Tab Buttons */}
            <div className="flex items-center bg-slate-100 dark:bg-slate-800 p-1 rounded-xl text-xs font-semibold">
              <button
                onClick={() => setActiveTab('original')}
                className={`px-3 py-1 rounded-lg transition-all ${
                  activeTab === 'original'
                    ? 'bg-white dark:bg-slate-700 text-teal-700 dark:text-teal-300 shadow-2xs font-bold'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                Original Document
              </button>
              <button
                onClick={() => setActiveTab('ocr')}
                className={`px-3 py-1 rounded-lg transition-all ${
                  activeTab === 'ocr'
                    ? 'bg-white dark:bg-slate-700 text-teal-700 dark:text-teal-300 shadow-2xs font-bold'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                Extracted Text
              </button>
              <button
                onClick={() => setActiveTab('structured')}
                className={`px-3 py-1 rounded-lg transition-all ${
                  activeTab === 'structured'
                    ? 'bg-white dark:bg-slate-700 text-teal-700 dark:text-teal-300 shadow-2xs font-bold'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                Structured Data
              </button>
            </div>

            {allowDownload && downloadUrl && (
              <a
                href={downloadUrl}
                target="_blank"
                rel="noreferrer"
                download
                className="p-2 rounded-xl text-slate-500 hover:text-teal-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                title="Download Original File"
              >
                <Download className="w-4 h-4" />
              </a>
            )}

            <button
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Viewer Content Area */}
        <div className="flex-1 bg-slate-100/70 dark:bg-slate-950 overflow-hidden flex flex-col relative">
          {activeTab === 'original' && (
            <div className="flex-1 flex flex-col overflow-hidden relative">
              {/* Zoom and Toolbar (for images & documents) */}
              <div className="px-4 py-2 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs shrink-0">
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-slate-700 dark:text-slate-300">Preview:</span>
                  <span className="text-[11px] font-mono text-slate-400 uppercase">
                    {mimeType || (isPdf ? 'PDF Document' : 'Clinical Image')}
                  </span>
                </div>

                <div className="flex items-center space-x-2">
                  {isImage && (
                    <>
                      <button
                        onClick={handleZoomOut}
                        disabled={zoomLevel <= 0.5}
                        className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300"
                        title="Zoom Out"
                      >
                        <ZoomOut className="w-3.5 h-3.5" />
                      </button>
                      <span className="text-[11px] font-mono font-bold text-slate-600 dark:text-slate-300 min-w-[40px] text-center">
                        {Math.round(zoomLevel * 100)}%
                      </span>
                      <button
                        onClick={handleZoomIn}
                        disabled={zoomLevel >= 3}
                        className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300"
                        title="Zoom In"
                      >
                        <ZoomIn className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={handleResetZoom}
                        className="p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500"
                        title="Reset Zoom"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                      </button>
                    </>
                  )}

                  {previewUrl && (
                    <a
                      href={previewUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center space-x-1 px-2.5 py-1 bg-slate-100 dark:bg-slate-800 hover:bg-teal-50 text-slate-700 dark:text-slate-300 text-[11px] font-semibold rounded-lg transition-colors"
                    >
                      <span>Open New Window</span>
                      <ExternalLink className="w-3 h-3 text-slate-400" />
                    </a>
                  )}
                </div>
              </div>

              {/* Viewport */}
              <div className="flex-1 overflow-auto p-4 flex items-center justify-center relative bg-slate-900/10 dark:bg-slate-950">
                {previewError ? (
                  <div className="text-center p-8 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-md max-w-sm space-y-3">
                    <AlertCircle className="w-8 h-8 text-rose-500 mx-auto" />
                    <h4 className="text-sm font-bold text-slate-800 dark:text-white">
                      Unable to open this document
                    </h4>
                    <p className="text-xs text-slate-500">
                      The file could not be rendered inline. You can download the original or retry loading.
                    </p>
                    <div className="pt-2 flex items-center justify-center space-x-2">
                      <button
                        onClick={() => {
                          setPreviewError(false);
                          setIsLoadingPreview(true);
                          onRetry?.();
                        }}
                        className="px-3 py-1.5 bg-teal-600 text-white text-xs font-bold rounded-xl shadow-xs inline-flex items-center space-x-1"
                      >
                        <RefreshCw className="w-3.5 h-3.5" />
                        <span>Retry</span>
                      </button>
                      {allowDownload && downloadUrl && (
                        <a
                          href={downloadUrl}
                          target="_blank"
                          rel="noreferrer"
                          download
                          className="px-3 py-1.5 border border-slate-200 dark:border-slate-700 text-xs font-semibold rounded-xl text-slate-700 dark:text-slate-300"
                        >
                          Download
                        </a>
                      )}
                    </div>
                  </div>
                ) : isPdf ? (
                  <iframe
                    src={previewUrl}
                    className="w-full h-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white"
                    title="PDF Document Preview"
                    onError={() => setPreviewError(true)}
                  />
                ) : (
                  <div
                    className="transition-transform duration-150 flex items-center justify-center max-w-full max-h-full"
                    style={{ transform: `scale(${zoomLevel})` }}
                  >
                    <img
                      src={previewUrl}
                      alt={title || 'Medical Record Preview'}
                      className="max-h-[75vh] max-w-full object-contain rounded-xl shadow-lg border border-slate-200 dark:border-slate-800 bg-white"
                      onError={() => setPreviewError(true)}
                    />
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'ocr' && (
            <div className="flex-1 p-6 overflow-y-auto bg-white dark:bg-slate-900 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white font-heading">
                    Raw Optical Character Recognition (OCR) Stream
                  </h3>
                  <p className="text-xs text-slate-400">
                    Dual-pass digitized text stream parsed from original medical imaging/PDF.
                  </p>
                </div>
                <button
                  onClick={handleCopyOcr}
                  disabled={!docData.ocr_raw_text}
                  className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-700 text-xs font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-50 transition-colors shadow-2xs"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copied ? 'Copied' : 'Copy Text'}</span>
                </button>
              </div>

              {docData.ocr_raw_text ? (
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/90 dark:border-slate-700 font-mono text-xs text-slate-800 dark:text-slate-200 whitespace-pre-wrap leading-relaxed">
                  {docData.ocr_raw_text}
                </div>
              ) : (
                <div className="p-12 text-center text-slate-400 text-xs">
                  No OCR text available for this document.
                </div>
              )}
            </div>
          )}

          {activeTab === 'structured' && (
            <div className="flex-1 p-6 overflow-y-auto bg-white dark:bg-slate-900 space-y-6">
              {/* Prescriptions */}
              {docData.prescriptions && docData.prescriptions.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-teal-700 dark:text-teal-400 flex items-center space-x-1.5 font-heading">
                    <Pill className="w-4 h-4" />
                    <span>Extracted Medications ({docData.prescriptions.length})</span>
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {docData.prescriptions.map((p, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-1 text-xs"
                      >
                        <p className="font-bold text-slate-900 dark:text-white">
                          {p.medication_name || p.drug_name}
                        </p>
                        <p className="text-slate-500 font-medium">
                          Dosage: {p.dosage || 'Standard'} • Frequency: {p.frequency || 'As directed'}
                        </p>
                        {p.timing_instructions && (
                          <p className="text-[11px] text-teal-600">Timing: {p.timing_instructions}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Lab Tests */}
              {docData.lab_tests && docData.lab_tests.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-teal-700 dark:text-teal-400 flex items-center space-x-1.5 font-heading">
                    <FlaskConical className="w-4 h-4" />
                    <span>Extracted Laboratory Biomarkers ({docData.lab_tests.length})</span>
                  </h4>
                  <div className="overflow-x-auto rounded-xl border border-slate-200/90 dark:border-slate-800">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 border-b border-slate-200 dark:border-slate-700">
                        <tr>
                          <th className="p-3 font-bold">Biomarker</th>
                          <th className="p-3 font-bold">Observed Value</th>
                          <th className="p-3 font-bold">Reference Range</th>
                          <th className="p-3 font-bold">Flag</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                        {docData.lab_tests.map((l, idx) => (
                          <tr key={idx} className="hover:bg-slate-50/60">
                            <td className="p-3 font-bold text-slate-900 dark:text-white">{l.test_name}</td>
                            <td className="p-3 font-bold text-teal-700">{l.observed_value} {l.unit}</td>
                            <td className="p-3 text-slate-500">{l.reference_range_text || 'Standard'}</td>
                            <td className="p-3">
                              <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${
                                l.flag === 'high' || l.flag === 'critical'
                                  ? 'bg-rose-50 text-rose-700 border border-rose-200'
                                  : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              }`}>
                                {l.flag || 'normal'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {(!docData.prescriptions || docData.prescriptions.length === 0) &&
                (!docData.lab_tests || docData.lab_tests.length === 0) && (
                  <div className="p-12 text-center text-slate-400 text-xs">
                    No discrete clinical entities extracted. Full document is available in Raw OCR and RAG search.
                  </div>
                )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReportViewer;
