import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useOutletContext } from 'react-router-dom';
import api from '../services/api';
import { generateClientChatResponse } from '../services/clientRAGService';
import { getStoredDocuments, openDocumentPreview } from '../services/documentStore';
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
  Clock,
  Plus,
  Trash2,
  History,
  Image as ImageIcon,
  Check
} from 'lucide-react';

const SUGGESTED_PROMPTS = [
  'What foods help with my health? 🥗',
  'What are my latest lab values? 🩺',
  'What did the report extract? 📄',
  'What changed from my last report? 📈',
  'What medicines am I taking? 💊',
  'Show my fasting glucose level 🩸',
  'Explain my latest report in simple words'
];

const createDefaultSession = (userName = 'there') => ({
  id: 'session_' + Date.now(),
  title: 'Welcome & Health Overview',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  messages: [
    {
      id: 'welcome_' + Date.now(),
      sender: 'ai',
      text: `Hey ${userName}! 👋 I'm HealthMate, your friendly personal health companion!\n\nI'm here to help you understand your health records, track your lab values, explain your medications, suggest healthy foods based on your reports, and answer any wellness questions — like a good friend who knows health! 🌟🥗\n\nYou can also take a photo of a medical report or prescription and I'll read it for you! 📸\n\nWhat would you like to know today?`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      citations: [],
      sources: [],
      evidence_status: 'SUPPORTED',
      structured_cards: [],
      follow_up_suggestions: [
        'What foods help with my health? 🥗',
        'What are my latest lab values? 🩺',
        'What did the report extract? 📄'
      ]
    }
  ]
});

const loadSavedSessions = (userName) => {
  try {
    const raw = localStorage.getItem('healthmate_chat_sessions');
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed;
      }
    }
  } catch (e) {
    console.error('Failed to load chat sessions:', e);
  }
  const initial = [createDefaultSession(userName)];
  try {
    localStorage.setItem('healthmate_chat_sessions', JSON.stringify(initial));
  } catch (e) {}
  return initial;
};

const AIAssistantPage = () => {
  const { user } = useAuth();
  const userName = user?.full_name?.split(' ')[0] || 'friend';
  const { openUpload } = useOutletContext() || {};

  // Chat History & Sessions
  const [sessions, setSessions] = useState(() => loadSavedSessions(userName));
  const [activeSessionId, setActiveSessionId] = useState(() => {
    const saved = localStorage.getItem('healthmate_active_session_id');
    const existing = loadSavedSessions(userName);
    if (saved && existing.some((s) => s.id === saved)) return saved;
    return existing[0]?.id || 'session_default';
  });
  const [showHistorySidebar, setShowHistorySidebar] = useState(false);

  // Active chat state
  const activeSession = sessions.find((s) => s.id === activeSessionId) || sessions[0] || createDefaultSession(userName);
  const messages = activeSession.messages || [];

  const [inputQuery, setInputQuery] = useState('');
  const [selectedLang, setSelectedLang] = useState('en');
  const [isTyping, setIsTyping] = useState(false);
  const [activeSourceModal, setActiveSourceModal] = useState(null);
  const [expandedSources, setExpandedSources] = useState({});
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const imageInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, activeSessionId]);

  // Save sessions to localStorage
  const updateCurrentSessionMessages = (newMessages, customTitle = null) => {
    setSessions((prevSessions) => {
      const updated = prevSessions.map((s) => {
        if (s.id === activeSessionId) {
          let title = s.title;
          if (customTitle) {
            title = customTitle;
          } else if (s.title === 'Welcome & Health Overview' || s.title === 'New Conversation') {
            const firstUser = newMessages.find((m) => m.sender === 'user');
            if (firstUser) {
              title = firstUser.text.length > 28 ? firstUser.text.slice(0, 28) + '...' : firstUser.text;
            }
          }
          return {
            ...s,
            title,
            updated_at: new Date().toISOString(),
            messages: newMessages
          };
        }
        return s;
      });
      try {
        localStorage.setItem('healthmate_chat_sessions', JSON.stringify(updated));
      } catch (e) {}
      return updated;
    });
  };

  const handleNewChat = () => {
    const newSession = {
      id: 'session_' + Date.now(),
      title: 'New Conversation',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      messages: [
        {
          id: 'welcome_' + Date.now(),
          sender: 'ai',
          text: `Hey ${userName}! 😊 Ready for a fresh start. Ask me anything about your diet 🥗, lab test results 🩺, medications 💊, or general wellness. How can I help you today?`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          citations: [],
          sources: [],
          evidence_status: 'SUPPORTED',
          structured_cards: [],
          follow_up_suggestions: [
            'What foods help with my health? 🥗',
            'What are my latest lab values? 🩺',
            'What did the report extract? 📄'
          ]
        }
      ]
    };
    const updated = [newSession, ...sessions];
    setSessions(updated);
    setActiveSessionId(newSession.id);
    localStorage.setItem('healthmate_chat_sessions', JSON.stringify(updated));
    localStorage.setItem('healthmate_active_session_id', newSession.id);
    setShowHistorySidebar(false);
  };

  const handleSelectSession = (sessionId) => {
    setActiveSessionId(sessionId);
    localStorage.setItem('healthmate_active_session_id', sessionId);
    setShowHistorySidebar(false);
  };

  const handleDeleteSession = (sessionId, e) => {
    e?.stopPropagation();
    if (sessions.length <= 1) {
      handleNewChat();
      return;
    }
    const filtered = sessions.filter((s) => s.id !== sessionId);
    setSessions(filtered);
    try {
      localStorage.setItem('healthmate_chat_sessions', JSON.stringify(filtered));
    } catch (err) {}
    if (activeSessionId === sessionId) {
      const nextActive = filtered[0]?.id || 'session_default';
      setActiveSessionId(nextActive);
      localStorage.setItem('healthmate_active_session_id', nextActive);
    }
  };

  const handleClearAllHistory = () => {
    if (!window.confirm('Are you sure you want to clear all chat history?')) return;
    const initial = [createDefaultSession(userName)];
    setSessions(initial);
    setActiveSessionId(initial[0].id);
    try {
      localStorage.setItem('healthmate_chat_sessions', JSON.stringify(initial));
      localStorage.setItem('healthmate_active_session_id', initial[0].id);
    } catch (e) {}
    setShowHistorySidebar(false);
  };

  const toggleSources = (msgId) => {
    setExpandedSources((prev) => ({
      ...prev,
      [msgId]: !prev[msgId]
    }));
  };

  const handleSend = async (queryText) => {
    const text = (queryText || inputQuery).trim();
    if ((!text && !imageFile) || isTyping) return;

    // Build user message
    const userMsg = {
      id: Date.now().toString(),
      sender: 'user',
      text: text || (imageFile ? '📸 [Sent an image for analysis]' : ''),
      imagePreview: imagePreview,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const newMessages = [...messages, userMsg];
    updateCurrentSessionMessages(newMessages);
    setInputQuery('');
    const currentImage = imageFile;
    const currentPreview = imagePreview;
    const currentText = text;
    setImageFile(null);
    setImagePreview(null);
    setIsTyping(true);

    try {
      let res;
      if (currentImage) {
        const formData = new FormData();
        formData.append('image', currentImage);
        formData.append('query', currentText || 'Analyze this medical image and extract all information.');
        formData.append('language', selectedLang);
        res = await api.post('/assistant/analyze-image', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      } else {
        res = await api.post('/assistant/chat', {
          query: currentText,
          language: selectedLang
        });
      }

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

      updateCurrentSessionMessages([...newMessages, aiMsg]);
    } catch (err) {
      console.warn('Backend chat unreachable, generating client-side RAG response from vault:', err);
      const clientFallback = generateClientChatResponse(currentText, selectedLang, currentPreview);
      const fallbackMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: clientFallback.answer,
        queryType: clientFallback.query_type,
        evidence_status: clientFallback.evidence_status || 'SUPPORTED',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations: clientFallback.citations || [],
        sources: clientFallback.sources || [],
        structured_cards: clientFallback.structured_cards || [],
        follow_up_suggestions: clientFallback.follow_up_suggestions || []
      };
      updateCurrentSessionMessages([...newMessages, fallbackMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleImageSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    const reader = new FileReader();
    reader.onload = (ev) => setImagePreview(ev.target.result);
    reader.readAsDataURL(file);
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
          <div className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-teal-50 text-teal-700 border border-teal-200/60 dark:bg-teal-950/60 dark:text-teal-300">
            <Sparkles className="w-3.5 h-3.5 text-teal-600 shrink-0" />
            <span>General Wellness Knowledge</span>
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
    <div className="h-[calc(100vh-8.5rem)] flex flex-col space-y-3">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowHistorySidebar((prev) => !prev)}
            className="p-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition flex items-center space-x-1.5 text-xs font-bold"
            title="Toggle Chat History"
          >
            <History className="w-4 h-4 text-teal-600" />
            <span>History ({sessions.length})</span>
          </button>

          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-extrabold uppercase tracking-widest text-teal-700 bg-teal-50 dark:bg-teal-950/60 px-2.5 py-0.5 rounded-full border border-teal-200/60 dark:border-teal-800/50">
                HealthMate AI
              </span>
              <span className="text-xs text-slate-400">
                • Your friendly health companion 🌟
              </span>
            </div>
            <h1 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-white font-heading tracking-tight mt-0.5">
              {activeSession?.title || 'AI Health Assistant'}
            </h1>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-2 flex-wrap gap-1.5 self-start sm:self-auto">
          <button
            onClick={handleNewChat}
            className="flex items-center space-x-1 px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold shadow-xs transition"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Chat</span>
          </button>

          {/* Trilingual Switcher */}
          <div className="flex items-center space-x-1 p-1 bg-white dark:bg-slate-800 rounded-xl border border-slate-200/90 dark:border-slate-700 text-xs shadow-2xs font-semibold">
            <Languages className="w-3.5 h-3.5 text-teal-600 ml-1.5" />
            <button
              onClick={() => setSelectedLang('en')}
              className={`px-2.5 py-1 rounded-lg transition-colors ${
                selectedLang === 'en' ? 'bg-teal-600 text-white font-bold' : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              EN
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
              Tanglish
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area: Split with Chat History Drawer */}
      <div className="flex-1 flex gap-4 overflow-hidden relative">
        {/* Chat History Sidebar / Overlay */}
        {showHistorySidebar && (
          <div className="w-72 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-xl flex flex-col overflow-hidden z-20 shrink-0 animate-in slide-in-from-left duration-150">
            <div className="p-3.5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <History className="w-4 h-4 text-teal-600" />
                <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider font-heading">
                  Chat History
                </h3>
              </div>
              <button
                onClick={() => setShowHistorySidebar(false)}
                className="p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-2 border-b border-slate-100 dark:border-slate-800">
              <button
                onClick={handleNewChat}
                className="w-full py-2 px-3 bg-teal-50 dark:bg-teal-950/60 text-teal-800 dark:text-teal-200 hover:bg-teal-100 rounded-xl text-xs font-bold flex items-center justify-center space-x-2 border border-teal-200 dark:border-teal-800 transition"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Start New Conversation</span>
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
              {sessions.map((sess) => {
                const isActive = sess.id === activeSessionId;
                return (
                  <div
                    key={sess.id}
                    onClick={() => handleSelectSession(sess.id)}
                    className={`p-2.5 rounded-xl cursor-pointer transition flex items-start justify-between group text-xs ${
                      isActive
                        ? 'bg-teal-600 text-white font-bold shadow-xs'
                        : 'hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300'
                    }`}
                  >
                    <div className="min-w-0 flex-1 pr-2">
                      <div className="flex items-center space-x-1.5">
                        <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-white' : 'text-teal-600'}`} />
                        <p className="truncate text-xs font-medium">{sess.title}</p>
                      </div>
                      <p className={`text-[10px] mt-0.5 ${isActive ? 'text-teal-100' : 'text-slate-400'}`}>
                        {new Date(sess.updated_at).toLocaleDateString([], { month: 'short', day: 'numeric' })} • {sess.messages?.length || 0} messages
                      </p>
                    </div>

                    <button
                      onClick={(e) => handleDeleteSession(sess.id, e)}
                      className={`p-1 rounded-lg opacity-0 group-hover:opacity-100 transition ${
                        isActive ? 'hover:bg-teal-700 text-white' : 'hover:bg-rose-50 text-rose-500'
                      }`}
                      title="Delete Conversation"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })}
            </div>

            <div className="p-3 border-t border-slate-100 dark:border-slate-800">
              <button
                onClick={handleClearAllHistory}
                className="w-full text-center text-[11px] text-rose-600 hover:underline font-semibold"
              >
                Clear All Conversations
              </button>
            </div>
          </div>
        )}

        {/* Chat Window */}
        <div className="flex-1 flex flex-col bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-2xs overflow-hidden">
          {/* Chat Messages Stream */}
          <div className="flex-1 p-4 sm:p-5 overflow-y-auto space-y-5">
            {messages.map((msg) => {
              const isUser = msg.sender === 'user';
              const citationList = msg.citations?.length ? msg.citations : msg.sources || [];
              const isSourcesOpen = expandedSources[msg.id] || false;

              return (
                <div key={msg.id} className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} space-y-2`}>
                  {/* Message Bubble */}
                  <div className={`flex items-start space-x-2.5 max-w-[92%] sm:max-w-[80%] ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
                    <div
                      className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
                        isUser
                          ? 'bg-slate-800 text-white dark:bg-slate-700'
                          : 'bg-teal-50 dark:bg-teal-950 text-teal-600 border border-teal-200/60 dark:border-teal-800'
                      }`}
                    >
                      {isUser ? <User className="w-4 h-4" /> : <BotMessageSquare className="w-4 h-4" />}
                    </div>

                    <div className="space-y-2">
                      <div
                        className={`p-4 rounded-2xl text-xs leading-relaxed shadow-2xs ${
                          isUser
                            ? 'bg-teal-600 text-white rounded-tr-none'
                            : 'bg-slate-50 dark:bg-slate-800/80 text-slate-800 dark:text-slate-200 rounded-tl-none border border-slate-200/60 dark:border-slate-700/60'
                        }`}
                      >
                        {msg.imagePreview && (
                          <div className="mb-3 rounded-xl overflow-hidden border border-white/20 max-w-xs">
                            <img src={msg.imagePreview} alt="Uploaded attachment" className="w-full h-auto object-cover" />
                          </div>
                        )}

                        <div className="whitespace-pre-wrap font-sans">{msg.text}</div>

                        <div className={`mt-2 flex items-center justify-between text-[10px] ${isUser ? 'text-teal-100' : 'text-slate-400'}`}>
                          <span>{msg.timestamp}</span>
                          {!isUser && msg.queryType && (
                            <span className="uppercase font-mono tracking-wider font-semibold text-[9px] ml-3">
                              {msg.queryType.replace(/_/g, ' ')}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* AI Structured Info Cards */}
                      {!isUser && msg.structured_cards?.length > 0 && (
                        <div className="flex items-center space-x-2 overflow-x-auto pb-1 pt-1 max-w-full">
                          {msg.structured_cards.map((c, i) => renderStructuredCard(c, i))}
                        </div>
                      )}

                      {/* Evidence Verification Badge & Citations */}
                      {!isUser && (
                        <div className="space-y-1.5">
                          <div className="flex items-center space-x-2">
                            {renderEvidenceStatusBadge(msg.evidence_status)}

                            {citationList.length > 0 && (
                              <button
                                onClick={() => toggleSources(msg.id)}
                                className="inline-flex items-center space-x-1 text-[10px] font-bold text-teal-600 hover:text-teal-700 bg-teal-50 dark:bg-teal-950/60 px-2 py-0.5 rounded-full border border-teal-200/50"
                              >
                                <span>{citationList.length} Verified Sources</span>
                                {isSourcesOpen ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                              </button>
                            )}
                          </div>

                          {/* Accordion Sources View */}
                          {isSourcesOpen && citationList.length > 0 && (
                            <div className="p-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2 mt-2">
                              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                                Verified Citations & Documents:
                              </span>
                              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                                {citationList.map((cite, idx) => (
                                  <div key={idx} className="py-2 first:pt-0 last:pb-0 flex items-start justify-between gap-3 text-xs">
                                    <div className="space-y-1 min-w-0">
                                      <div className="flex items-center space-x-1.5 flex-wrap gap-1">
                                        {getCitationBadge(cite.source_type)}
                                        <span className="font-bold text-slate-800 dark:text-slate-200 truncate">
                                          {cite.source_name || cite.name || 'Medical Document'}
                                        </span>
                                      </div>
                                      <p className="text-[11px] text-slate-500 font-mono line-clamp-2">
                                        "{cite.text_snippet || cite.snippet || 'Extracted clinical evidence'}"
                                      </p>
                                    </div>
                                    <button
                                      onClick={() => setActiveSourceModal(cite)}
                                      className="p-1.5 rounded-lg text-slate-400 hover:text-teal-600 hover:bg-slate-50 dark:hover:bg-slate-800 shrink-0"
                                      title="Inspect Source Record"
                                    >
                                      <Eye className="w-3.5 h-3.5" />
                                    </button>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Follow up Prompts */}
                      {!isUser && msg.follow_up_suggestions?.length > 0 && (
                        <div className="flex items-center flex-wrap gap-1.5 pt-1">
                          {msg.follow_up_suggestions.map((sug, i) => (
                            <button
                              key={i}
                              onClick={() => handleSend(sug)}
                              className="text-[11px] px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-teal-50 hover:text-teal-700 dark:hover:bg-teal-950/60 dark:hover:text-teal-300 transition-colors border border-slate-200/60 dark:border-slate-700/60 font-medium"
                            >
                              {sug}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}

            {isTyping && (
              <div className="flex items-center space-x-2 text-slate-400 text-xs">
                <div className="w-8 h-8 rounded-xl bg-teal-50 dark:bg-teal-950 text-teal-600 flex items-center justify-center animate-pulse">
                  <BotMessageSquare className="w-4 h-4" />
                </div>
                <div className="flex items-center space-x-1.5 bg-slate-50 dark:bg-slate-800 px-3.5 py-2 rounded-2xl border border-slate-200/60 dark:border-slate-700/60">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-teal-600" />
                  <span className="text-[11px] font-medium text-slate-500">Checking health vault & synthesizing friendly answer...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Suggestions Chips */}
          <div className="px-4 py-2 bg-slate-50/70 dark:bg-slate-800/40 border-t border-slate-100 dark:border-slate-800 flex items-center space-x-1.5 overflow-x-auto text-[11px] shrink-0">
            <span className="text-slate-400 font-bold uppercase text-[9px] tracking-wider shrink-0 flex items-center space-x-1">
              <Sparkles className="w-3 h-3 text-teal-600" />
              <span>Ask:</span>
            </span>
            {SUGGESTED_PROMPTS.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(prompt)}
                className="px-2.5 py-1 rounded-lg bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:text-teal-600 hover:border-teal-300 shrink-0 transition-colors whitespace-nowrap"
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Input Bar */}
          <div className="p-3 sm:p-4 border-t border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900 shrink-0">
            {imagePreview && (
              <div className="mb-2 p-2 bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <img src={imagePreview} alt="Preview" className="w-9 h-9 rounded-lg object-cover" />
                  <div>
                    <p className="text-xs font-bold text-slate-800 dark:text-slate-200">{imageFile?.name}</p>
                    <p className="text-[10px] text-teal-600 font-semibold">Ready for Vision OCR Analysis</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setImageFile(null);
                    setImagePreview(null);
                  }}
                  className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}

            <div className="flex items-center space-x-2">
              <input
                type="file"
                ref={imageInputRef}
                onChange={handleImageSelect}
                accept="image/*,.pdf"
                className="hidden"
              />

              <button
                type="button"
                onClick={() => imageInputRef.current?.click()}
                className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-500 hover:text-teal-600 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                title="Attach photo of medical report / prescription"
              >
                <ImageIcon className="w-4 h-4" />
              </button>

              <div className="flex-1 relative">
                <input
                  type="text"
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask a question (e.g. 'What foods help with my health? 🥗' or 'Explain my blood test')..."
                  className="w-full px-4 py-2.5 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200/90 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-teal-500/30 transition-all placeholder:text-slate-400"
                />
              </div>

              <button
                type="button"
                onClick={() => handleSend()}
                disabled={(!inputQuery.trim() && !imageFile) || isTyping}
                className="p-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 disabled:opacity-40 text-white transition-all shadow-xs active:scale-95"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Source Verification Modal */}
      {activeSourceModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="w-full max-w-lg bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200/90 dark:border-slate-800 overflow-hidden">
            <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-teal-600" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white font-heading">
                  Source Evidence Record
                </h3>
              </div>
              <button
                onClick={() => setActiveSourceModal(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 space-y-3.5 text-xs">
              <div>
                <span className="text-[10px] font-bold uppercase text-slate-400">Source Document</span>
                <p className="text-sm font-bold text-slate-900 dark:text-white mt-0.5">
                  {activeSourceModal.source_name || activeSourceModal.name || 'Medical Document'}
                </p>
                {activeSourceModal.page_number && (
                  <p className="text-[11px] text-slate-500 mt-0.5">Page {activeSourceModal.page_number}</p>
                )}
              </div>

              <div className="p-3.5 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700">
                <span className="text-[10px] font-bold uppercase text-teal-700 dark:text-teal-400">
                  Extracted Evidence Text
                </span>
                <p className="text-xs text-slate-800 dark:text-slate-200 mt-1.5 font-mono leading-relaxed bg-white dark:bg-slate-900 p-3 rounded-lg border border-slate-200 dark:border-slate-800">
                  "{activeSourceModal.text_snippet || activeSourceModal.snippet || 'Extracted clinical details'}"
                </p>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  onClick={() => {
                    const docs = getStoredDocuments();
                    const d = docs.find((x) => x.id === activeSourceModal.document_id || String(x.id) === String(activeSourceModal.document_id)) || {
                      id: activeSourceModal.document_id || 'doc',
                      title: activeSourceModal.source_name || activeSourceModal.name || 'Document',
                      ocr_raw_text: activeSourceModal.text_snippet
                    };
                    openDocumentPreview(d);
                  }}
                  className="inline-flex items-center space-x-1.5 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl shadow-xs transition-all"
                >
                  <span>Open Original File</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIAssistantPage;
