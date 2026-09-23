import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import {
  Search,
  FlaskConical,
  Pill,
  FileText,
  Activity,
  Layers,
  ExternalLink,
  Loader2,
  X
} from 'lucide-react';

const GlobalSearchBar = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const searchRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!query.trim() || query.length < 2) {
      setResults(null);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        setIsLoading(true);
        const res = await api.get('/health-search', { params: { q: query.trim() } });
        setResults(res.data);
        setIsOpen(true);
      } catch (err) {
        console.error('Search error:', err);
      } finally {
        setIsLoading(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectResult = (item) => {
    setIsOpen(false);
    if (item.result_type === 'LAB_TEST' || item.result_type === 'DOCUMENT' || item.result_type === 'DOCUMENT_CHUNK') {
      navigate('/reports');
    } else if (item.result_type === 'PRESCRIPTION') {
      navigate('/prescriptions');
    } else {
      navigate('/records');
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'LAB_TEST':
        return <FlaskConical className="w-3.5 h-3.5 text-teal-600" />;
      case 'PRESCRIPTION':
        return <Pill className="w-3.5 h-3.5 text-teal-600" />;
      case 'DOCUMENT':
        return <FileText className="w-3.5 h-3.5 text-teal-600" />;
      case 'DOCUMENT_CHUNK':
        return <Layers className="w-3.5 h-3.5 text-sky-600" />;
      default:
        return <Activity className="w-3.5 h-3.5 text-slate-500" />;
    }
  };

  return (
    <div className="relative flex-1 max-w-xs sm:max-w-sm md:max-w-md hidden md:block" ref={searchRef}>
      <div className="relative">
        <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query.length >= 2 && setIsOpen(true)}
          placeholder="Global EHR Search (e.g. Glucose, Amoxicillin, CBC)..."
          className="w-full pl-9 pr-8 py-2 bg-slate-100/80 dark:bg-slate-800/80 text-slate-900 dark:text-slate-100 placeholder-slate-400 text-xs rounded-xl border border-transparent focus:border-teal-500/40 focus:bg-white dark:focus:bg-slate-900 focus:outline-none transition-all"
        />
        {isLoading ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin text-teal-600 absolute right-3 top-1/2 -translate-y-1/2" />
        ) : query ? (
          <button
            onClick={() => {
              setQuery('');
              setResults(null);
            }}
            className="p-1 rounded text-slate-400 hover:text-slate-600 absolute right-2 top-1/2 -translate-y-1/2"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        ) : null}
      </div>

      {/* Results Popover matching global-search.png */}
      {isOpen && results && (
        <div className="absolute left-0 right-0 mt-2 bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200/90 dark:border-slate-800 z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-100 max-h-96 overflow-y-auto">
          <div className="px-4 py-2.5 bg-slate-50/80 dark:bg-slate-800/80 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px]">
            <span className="font-bold text-slate-700 dark:text-slate-300">
              Found {results.total_results} matching patient records
            </span>
            <span className="text-slate-400">
              {results.structured_count} structured • {results.semantic_count} semantic
            </span>
          </div>

          {results.total_results === 0 ? (
            <div className="p-6 text-center text-slate-400">
              <Search className="w-6 h-6 mx-auto mb-2 opacity-40" />
              <p className="text-xs font-semibold">No matching medical records found.</p>
              <p className="text-[10px] mt-0.5">Try searching by lab test name, medicine, date, or hospital.</p>
            </div>
          ) : (
            <div className="p-1.5 divide-y divide-slate-100 dark:divide-slate-800">
              {results.results.map((item, idx) => (
                <div
                  key={idx}
                  onClick={() => handleSelectResult(item)}
                  className="p-2.5 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-2.5">
                      <div className="p-1.5 rounded-lg bg-teal-50 dark:bg-teal-950 text-teal-600 shrink-0 mt-0.5">
                        {getIcon(item.result_type)}
                      </div>
                      <div>
                        <p className="text-xs font-bold text-slate-900 dark:text-white">
                          {item.title}
                        </p>
                        {item.subtitle && (
                          <p className="text-[11px] text-slate-600 dark:text-slate-300 mt-0.5">
                            {item.subtitle}
                          </p>
                        )}
                        {item.snippet && item.result_type === 'DOCUMENT_CHUNK' && (
                          <p className="text-[10px] text-slate-400 mt-1 italic line-clamp-2">
                            "{item.snippet}"
                          </p>
                        )}
                        <div className="flex items-center space-x-2 mt-1 text-[10px] text-slate-400">
                          {item.date && <span>Date: {item.date}</span>}
                          {item.source_document_title && (
                            <>
                              <span>•</span>
                              <span className="truncate max-w-[180px]">Source: {item.source_document_title}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    <span className="text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 shrink-0">
                      {item.result_type.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default GlobalSearchBar;
