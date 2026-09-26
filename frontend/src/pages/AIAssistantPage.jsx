import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useOutletContext, Link } from 'react-router-dom';
import api from '../services/api';
import {
  BotMessageSquare,
  Send,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  Languages,
  FileText,
  User,
  Info,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  ExternalLink,
  BookOpen,
  Database,
  Eye,
  X,
  Highlighter,
  ChevronDown,
  ChevronUp,
  FlaskConical,
  Pill,
  Activity,
  TrendingUp,
  TrendingDown,
  Minus,
  PlusCircle,
  CornerDownLeft,
  Loader2,
  MessageSquare,
  Clock
} from 'lucide-react';

const SUGGESTED_PROMPTS = [
  'What are my latest values?',
  'What changed from my previous report?',
  'What medicines are listed?',
  'Show my glucose history.',
  'What was my glucose in March?',
  'Explain my latest report.',
  'What is glucose and what are normal ranges?'
];

const AIAssistantPage = () => {
  const { user } = useAuth();
  const { openUpload } = useOutletContext() || {};
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'ai',
      text: `Hello ${user?.full_name || 'Patient'}! I am your HealthMate Clinical AI Assistant.\n\nI can help you review and analyze your verified personal medical records, track longitudinal biomarker trends, review prescribed medicines, and cross-reference clinical ranges in English, தமிழ், or Multilanguage.`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      citations: [],
      sources: [],
      evidence_status: 'SUPPORTED',
      structured_cards: [],
      follow_up_suggestions: [
        'What are my latest values?',
        'What changed from my previous report?',
        'What medicines are listed?'
      ]
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [selectedLang, setSelectedLang] = useState('en');
  const [isTyping, setIsTyping] = useState(false);
  const [activeSourceModal, setActiveSourceModal] = useState(null);
  const [expandedSources, setExpandedSources] = useState({});
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const toggleSources = (msgId) => {
    setExpandedSources((prev) => ({
      ...prev,
      [msgId]: !prev[msgId]
    }));
  };

  const handleSend = async (queryText) => {
    const text = (queryText || inputQuery).trim();
    if (!text || isTyping) return;

    const userMsg = {
      id: Date.now().toString(),
      sender: 'user',
      text: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setIsTyping(true);

    try {
      const res = await api.post('/assistant/chat', {
        query: text,
        language: selectedLang
      });

      const data = res.data;
      const aiMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: data.answer,
        queryType: data.query_type,
        priorityApplied: data.evidence_priority_applied,
        evidence_status: data.evidence_status || (data.evidence_found ? 'SUPPORTED' : 'INSUFFICIENT'),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations: data.citations || data.sources || [],
        sources: data.sources || data.citations || [],
        structured_cards: data.structured_cards || [],
        follow_up_suggestions: data.follow_up_suggestions || []
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      console.error('Chat error:', err);
      const errMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: "Sorry, I couldn't retrieve your health records right now. Please try again or verify your connection.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations: [],
        sources: [],
        evidence_status: 'INSUFFICIENT',
        structured_cards: [],
        follow_up_suggestions: ['What are my latest values?', 'What is glucose?']
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const renderEvidenceStatusBadge = (status) => {
    switch (status) {
      case 'SUPPORTED':
        return (
          <div className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200/60 dark:bg-emerald-950/60 dark:text-emerald-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span>Supported by verified records</span>
          </div>
        );
      case 'PARTIAL':
        return (
          <div className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200/60 dark:bg-amber-950/60 dark:text-amber-300">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
            <span>Partially supported by available records</span>
          </div>
        );
      case 'INSUFFICIENT':
        return (
          <div className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200/60 dark:bg-rose-950/60 dark:text-rose-300">
            <AlertCircle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
            <span>No matching evidence in available records</span>
          </div>
        );
      default:
        return null;
    }
  };

  const renderStructuredCard = (card, idx) => {
    if (card.card_type === 'VALUE_CARD') {
      return (
        <div
          key={idx}
          className="p-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-200/90 dark:border-slate-700 shadow-2xs flex items-center justify-between gap-3 min-w-[200px]"
        >
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-lg bg-teal-50 dark:bg-teal-950 text-teal-600 shrink-0">
              <FlaskConical className="w-4 h-4" />
            </div>
            <div>
              <p className="text-xs font-bold text-slate-900 dark:text-white">{card.title}</p>
              <p className="text-[10px] text-slate-400">{card.date}</p>
            </div>
          </div>
          <div className="text-right">
            <span className="text-xs font-black text-teal-700 dark:text-teal-400">
              {card.value} {card.unit}
            </span>
            <span className="block text-[9px] font-bold uppercase text-slate-400">{card.flag}</span>
          </div>
        </div>
      );
    } else if (card.card_type === 'PRESCRIPTION_CARD') {
      return (
        <div
          key={idx}
          className="p-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-200/90 dark:border-slate-700 shadow-2xs space-y-1.5 min-w-[220px]"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1.5">
              <Pill className="w-3.5 h-3.5 text-teal-600" />
              <span className="text-xs font-bold text-slate-900 dark:text-white">{card.title}</span>
            </div>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200/60">
              {card.dosage}
            </span>
          </div>
          <p className="text-[10px] text-slate-500">
            {card.frequency} • {card.timing}
          </p>
        </div>
      );
    } else if (card.card_type === 'TREND_CARD') {
      return (
        <div
          key={idx}
          className="p-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-200/90 dark:border-slate-700 shadow-2xs space-y-1 min-w-[220px]"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-900 dark:text-white">{card.title}</span>
            <span className="text-[10px] font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
              {card.percentage_change}
            </span>
          </div>
          <p className="text-xs font-bold text-teal-700">
            {card.previous_value} {card.unit} → {card.latest_value} {card.unit}
          </p>
        </div>
      );
    }
    return null;
  };

  const getCitationBadge = (sourceType) => {
    switch (sourceType) {
      case 'USER_STRUCTURED_RECORD':
        return (
          <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-teal-50 text-teal-700 border border-teal-200 flex items-center space-x-1">
            <Database className="w-3 h-3" />
            <span>Vault Record</span>
          </span>
        );
      case 'USER_DOCUMENT_CHUNK':
        return (
          <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-sky-50 text-sky-700 border border-sky-200 flex items-center space-x-1">
            <FileText className="w-3 h-3" />
            <span>Document OCR Chunk</span>
          </span>
        );
      case 'GENERAL_MEDICAL_KNOWLEDGE':
        return (
          <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-purple-50 text-purple-700 border border-purple-200 flex items-center space-x-1">
            <BookOpen className="w-3 h-3" />
            <span>Clinical Knowledge</span>
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-slate-100 text-slate-700">
            <span>Verified Source</span>
          </span>
        );
    }
  };

  return (
    <div className="h-[calc(100vh-8.5rem)] flex flex-col space-y-4">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-[10px] font-extrabold uppercase tracking-widest text-teal-700 bg-teal-50 dark:bg-teal-950/60 px-2.5 py-0.5 rounded-full border border-teal-200/60 dark:border-teal-800/50">
              Evidence Guard Engine
            </span>
            <span className="text-xs text-slate-400">
              • Zero Hallucination Mode Active
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white font-heading tracking-tight mt-0.5">
            HealthMate Clinical AI Assistant
          </h1>
          <p className="text-xs text-slate-500">
            Query lab diagnostics, medication records, and historical changes with verbatim source citations.
          </p>
        </div>

        {/* Trilingual Switcher */}
        <div className="flex items-center space-x-1 p-1 bg-white dark:bg-slate-800 rounded-xl border border-slate-200/90 dark:border-slate-700 text-xs self-start sm:self-auto shadow-2xs font-semibold">
          <Languages className="w-3.5 h-3.5 text-teal-600 ml-1.5" />
          <button
            onClick={() => setSelectedLang('en')}
            className={`px-2.5 py-1 rounded-lg transition-colors ${
              selectedLang === 'en' ? 'bg-teal-600 text-white font-bold' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            English
          </button>
          <button
            onClick={() => setSelectedLang('ta')}
            className={`px-2.5 py-1 rounded-lg transition-colors ${
              selectedLang === 'ta' ? 'bg-teal-600 text-white font-bold' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            தமிழ்
          </button>
          <button
            onClick={() => setSelectedLang('tanglish')}
            className={`px-2.5 py-1 rounded-lg transition-colors ${
              selectedLang === 'tanglish' ? 'bg-teal-600 text-white font-bold' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Multilanguage
          </button>
        </div>
      </div>

      {/* Safety Notice */}
      <div className="p-3 rounded-2xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/60 text-xs text-amber-900 dark:text-amber-300 flex items-center space-x-2.5 shrink-0 shadow-2xs">
        <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600 dark:text-amber-400" />
        <p className="leading-tight">
          <strong>Clinical Copilot Protocol:</strong> Answers are retrieved strictly from your uploaded files with source chunk hashes. Non-prescriptive reference only.
        </p>
      </div>

      {/* Chat Messages Stream */}
      <div className="flex-1 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 p-5 overflow-y-auto space-y-5 shadow-2xs">
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          const citationList = msg.citations?.length ? msg.citations : msg.sources || [];
          const isSourcesOpen = expandedSources[msg.id] || false;

          return (
            <div
              key={msg.id}
              className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}
            >
              {/* Avatar */}
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 shadow-xs ${
                  isUser
                    ? 'bg-slate-900 dark:bg-slate-800 text-white'
                    : 'bg-teal-600 text-white'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <BotMessageSquare className="w-4 h-4" />}
              </div>

              {/* Message Content Bubble */}
              <div className={`space-y-2.5 max-w-2xl ${isUser ? 'items-end text-right' : 'items-start text-left'}`}>
                {!isUser && msg.id !== 'welcome' && (
                  <div>{renderEvidenceStatusBadge(msg.evidence_status)}</div>
                )}

                <div
                  className={`p-4 rounded-2xl text-xs leading-relaxed shadow-2xs ${
                    isUser
                      ? 'bg-teal-600 text-white rounded-tr-xs'
                      : 'bg-slate-50/80 dark:bg-slate-800/70 text-slate-900 dark:text-slate-100 rounded-tl-xs border border-slate-200/80 dark:border-slate-700/80 whitespace-pre-wrap'
                  }`}
                >
                  {msg.text}
                </div>

                {/* Structured Cards */}
                {!isUser && msg.structured_cards && msg.structured_cards.length > 0 && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                    {msg.structured_cards.map((c, i) => renderStructuredCard(c, i))}
                  </div>
                )}

                {/* Citations Box */}
                {!isUser && citationList.length > 0 && (
                  <div className="rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 overflow-hidden text-left">
                    <button
                      onClick={() => toggleSources(msg.id)}
                      className="w-full px-3.5 py-2 flex items-center justify-between text-[11px] font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700/50 transition-colors"
                    >
                      <div className="flex items-center space-x-1.5">
                        <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
                        <span>Evidence Sources & RE EHR Paths ({citationList.length})</span>
                      </div>
                      {isSourcesOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>

                    {isSourcesOpen && (
                      <div className="p-3 pt-0 space-y-2 divide-y divide-slate-200 dark:divide-slate-700">
                        {citationList.map((c, i) => (
                          <div key={i} className="pt-2 text-[11px] space-y-1.5">
                            <div className="flex items-center justify-between gap-2 flex-wrap">
                              <div className="flex items-center space-x-2">
                                {getCitationBadge(c.source_type)}
                                <span className="font-bold text-slate-800 dark:text-slate-200 truncate max-w-[200px]">
                                  {c.source_name}
                                </span>
                              </div>

                              <button
                                onClick={() => setActiveSourceModal(c)}
                                className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-lg bg-teal-50 hover:bg-teal-100 text-teal-700 font-bold text-[10px] transition-colors"
                              >
                                <span>[Inspect Snippet]</span>
                                <Eye className="w-3 h-3" />
                              </button>
                            </div>
                            <p className="text-[10px] text-slate-600 dark:text-slate-400 italic bg-white dark:bg-slate-900 p-2 rounded-lg border border-slate-200/80 dark:border-slate-800">
                              "{c.text_snippet}"
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Follow-up Suggestions */}
                {!isUser && msg.follow_up_suggestions && msg.follow_up_suggestions.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {msg.follow_up_suggestions.map((sug, i) => (
                      <button
                        key={i}
                        onClick={() => handleSend(sug)}
                        className="px-3 py-1 rounded-full text-[11px] font-semibold bg-teal-50 hover:bg-teal-100 text-teal-800 dark:bg-teal-950/60 dark:text-teal-300 border border-teal-200/60 transition-colors shadow-2xs"
                      >
                        {sug}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {isTyping && (
          <div className="flex items-start space-x-3">
            <div className="w-9 h-9 rounded-xl bg-teal-600 text-white flex items-center justify-center shrink-0 shadow-xs">
              <BotMessageSquare className="w-4 h-4" />
            </div>
            <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/70 border border-slate-200/80 text-xs text-slate-500 flex items-center space-x-2">
              <Loader2 className="w-4 h-4 animate-spin text-teal-600" />
              <span>Verifying patient records & evidence snippets...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts */}
      {messages.length <= 1 && (
        <div className="flex items-center space-x-2 overflow-x-auto pb-1 shrink-0 scrollbar-none">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider shrink-0">
            Suggested:
          </span>
          {SUGGESTED_PROMPTS.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(prompt)}
              className="px-3 py-1 rounded-xl text-xs font-semibold bg-white hover:bg-teal-50 dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200/90 dark:border-slate-700 shrink-0 transition-colors shadow-2xs"
            >
              {prompt}
            </button>
          ))}
        </div>
      )}

      {/* Input Bar */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 p-2 shadow-2xs shrink-0 flex items-center space-x-2">
        <textarea
          ref={textareaRef}
          rows={1}
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a clinical question about your lab tests or medications..."
          className="flex-1 px-3 py-1.5 bg-transparent text-slate-900 dark:text-white placeholder-slate-400 text-xs resize-none focus:outline-none max-h-24"
        />
        <button
          onClick={() => handleSend()}
          disabled={!inputQuery.trim() || isTyping}
          className="p-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl active:scale-95 disabled:opacity-40 disabled:pointer-events-none transition-all shadow-xs"
          aria-label="Send query"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>

      {/* Source Highlighting Modal */}
      {activeSourceModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xl max-w-lg w-full overflow-hidden">
            <div className="p-5 bg-teal-600 text-white flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <Highlighter className="w-5 h-5 text-teal-200" />
                <h3 className="text-sm font-bold font-heading">Evidence Grounding & Source Snippet</h3>
              </div>
              <button
                onClick={() => setActiveSourceModal(null)}
                className="p-1 rounded-full hover:bg-white/20 text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <span className="text-[10px] font-bold uppercase text-slate-400">Source Document</span>
                <p className="text-sm font-bold text-slate-900 dark:text-white">
                  {activeSourceModal.source_name}
                </p>
                {activeSourceModal.page_number && (
                  <p className="text-xs text-slate-500">Page {activeSourceModal.page_number}</p>
                )}
              </div>

              <div className="p-4 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700">
                <span className="text-[10px] font-bold uppercase text-teal-700 dark:text-teal-400">
                  Extracted Evidence Text
                </span>
                <p className="text-xs text-slate-800 dark:text-slate-200 mt-1.5 font-mono leading-relaxed bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-800">
                  "{activeSourceModal.text_snippet}"
                </p>
              </div>

              {activeSourceModal.document_id && (
                <div className="pt-2 flex justify-end">
                  <a
                    href={`/api/v1/documents/${activeSourceModal.document_id}/download`}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center space-x-1.5 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl shadow-xs transition-all"
                  >
                    <span>Open Original File</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIAssistantPage;
