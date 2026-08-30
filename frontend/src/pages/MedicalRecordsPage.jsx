import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import api from '../services/api';
import DocumentDetailModal from '../components/common/DocumentDetailModal';
import {
  FolderOpen,
  Search,
  PlusCircle,
  FileText,
  FlaskConical,
  Pill,
  Activity,
  Download,
  Eye,
  Trash2,
  ShieldCheck,
  Calendar,
  User,
  Building,
  AlertCircle,
  X,
  Loader2
} from 'lucide-react';

const CATEGORY_TABS = [
  { id: 'all', label: 'All Documents' },
  { id: 'lab_report', label: 'Lab Reports', icon: FlaskConical },
  { id: 'prescription', label: 'Prescriptions', icon: Pill },
  { id: 'imaging', label: 'Radiology / X-Ray', icon: Activity },
  { id: 'discharge_summary', label: 'Discharge Summaries', icon: FileText },
  { id: 'other', label: 'Other Records', icon: FolderOpen },
];

const MedicalRecordsPage = () => {
  const { openUpload } = useOutletContext();
  const [documents, setDocuments] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);

  const fetchDocuments = async () => {
    try {
      setIsLoading(true);
      const params = {};
      if (selectedCategory !== 'all') params.category = selectedCategory;
      if (searchQuery.trim()) params.search = searchQuery.trim();
      const res = await api.get('/documents/', { params });
      setDocuments(res.data || []);
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
    const handleRefresh = () => fetchDocuments();
    window.addEventListener('healthmate_doc_uploaded', handleRefresh);
    return () => window.removeEventListener('healthmate_doc_uploaded', handleRefresh);
  }, [selectedCategory, searchQuery]);

  const handleDelete = async (docId) => {
    try {
      await api.delete(`/documents/${docId}`);
      setDocuments(documents.filter((d) => d.id !== docId));
      setDeleteConfirmId(null);
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  const handleDownload = (doc) => {
    const token = localStorage.getItem('healthmate_access_token');
    window.open(`/api/v1/documents/${doc.id}/download?token=${token}`, '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white font-heading">
            Medical Records Vault
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Immutable, SHA-256 hashed medical records repository
          </p>
        </div>

        <button
          onClick={openUpload}
          className="inline-flex items-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-brand-600 to-cyan-600 hover:from-brand-700 hover:to-cyan-700 text-white text-xs font-semibold rounded-xl shadow-md shadow-brand-500/20 transition-all active:scale-95 self-start sm:self-auto"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Upload Record</span>
        </button>
      </div>

      {/* Category Tabs & Search Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 max-w-full">
          {CATEGORY_TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setSelectedCategory(tab.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all ${
                selectedCategory === tab.id
                  ? 'bg-brand-600 text-white font-semibold shadow-sm'
                  : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700/60 border border-slate-200 dark:border-slate-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="relative min-w-[240px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by title, doctor, lab..."
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500 text-slate-900 dark:text-white"
          />
        </div>
      </div>

      {/* Document Grid */}
      {isLoading ? (
        <div className="p-16 text-center bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
          <Loader2 className="w-7 h-7 animate-spin text-brand-600 mx-auto mb-2" />
          <p className="text-xs text-slate-500">Retrieving records from vault...</p>
        </div>
      ) : documents.length === 0 ? (
        <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 space-y-3">
          <FolderOpen className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto" />
          <div>
            <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
              No documents found in this view
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Upload a prescription, lab report, or hospital summary to get started.
            </p>
          </div>
          <button
            onClick={openUpload}
            className="inline-flex items-center space-x-1.5 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-xs font-semibold rounded-xl transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Upload Document</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:shadow-md hover:border-brand-300 dark:hover:border-brand-800 transition-all flex flex-col justify-between space-y-4"
            >
              <div className="space-y-2.5">
                <div className="flex items-start justify-between gap-2">
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-brand-50 dark:bg-brand-950/60 text-brand-700 dark:text-brand-300 border border-brand-200 dark:border-brand-800">
                    {doc.category.replace('_', ' ')}
                  </span>
                  <div className="flex items-center space-x-1 text-emerald-600 dark:text-emerald-400 text-[10px] font-semibold" title={`SHA-256: ${doc.file_hash_sha256}`}>
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>SHA-256 OK</span>
                  </div>
                </div>

                <h3 className="text-sm font-bold text-slate-900 dark:text-white leading-snug line-clamp-2">
                  {doc.title}
                </h3>

                <div className="space-y-1 text-xs text-slate-500">
                  {doc.document_date && (
                    <div className="flex items-center space-x-1.5">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      <span>Date: {doc.document_date}</span>
                    </div>
                  )}
                  {doc.doctor_name && (
                    <div className="flex items-center space-x-1.5">
                      <User className="w-3.5 h-3.5 text-slate-400" />
                      <span className="truncate">Dr: {doc.doctor_name}</span>
                    </div>
                  )}
                  {doc.clinic_or_lab && (
                    <div className="flex items-center space-x-1.5">
                      <Building className="w-3.5 h-3.5 text-slate-400" />
                      <span className="truncate">Lab: {doc.clinic_or_lab}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                <span className="text-[10px] text-slate-400">
                  {(doc.file_size_bytes / (1024 * 1024)).toFixed(2)} MB
                </span>

                <div className="flex items-center space-x-1">
                  <button
                    onClick={() => setSelectedDocId(doc.id)}
                    className="p-1.5 rounded-lg text-slate-500 hover:text-brand-600 dark:hover:text-brand-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                    title="View OCR & Clinical Details"
                  >
                    <Eye className="w-4 h-4" />
                  </button>

                  <button
                    onClick={() => handleDownload(doc)}
                    className="p-1.5 rounded-lg text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                    title="Download Verified File"
                  >
                    <Download className="w-4 h-4" />
                  </button>

                  <button
                    onClick={() => setDeleteConfirmId(doc.id)}
                    className="p-1.5 rounded-lg text-slate-500 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                    title="Delete Record"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirmId && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-200 dark:border-slate-800 space-y-4">
            <div className="flex items-center space-x-3 text-rose-600 dark:text-rose-400">
              <AlertCircle className="w-6 h-6" />
              <h3 className="text-base font-bold font-heading">Delete Medical Record?</h3>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              This will remove the file from your personal vault. This action is permanently audited.
            </p>
            <div className="flex justify-end space-x-2 pt-2">
              <button
                onClick={() => setDeleteConfirmId(null)}
                className="px-4 py-2 text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deleteConfirmId)}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-xl"
              >
                Confirm Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Document Detail & OCR Split-Screen Modal */}
      {selectedDocId && (
        <DocumentDetailModal
          docId={selectedDocId}
          isOpen={!!selectedDocId}
          onClose={() => setSelectedDocId(null)}
          onUpdated={fetchDocuments}
        />
      )}
    </div>
  );
};

export default MedicalRecordsPage;
