import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
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
  RefreshCw
} from 'lucide-react';

const SUGGESTED_PROMPTS = [
  'What are my latest HbA1c and blood glucose results?',
  'Explain my active prescription medications and food timings.',
  'Are any of my recent blood test parameters flagged abnormal?',
  'What Indian dietary foods can help manage my blood sugar level?',
  'Generate an appointment summary for my upcoming doctor visit.'
];

const AIAssistantPage = () => {
  const { user } = useAuth();
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'ai',
      text: `Hello ${user?.full_name || 'Patient'}, I am your HealthMate AI Medical Assistant. I provide evidence-grounded answers based strictly on your uploaded medical records in English, Tamil, and Tanglish. How can I help you today?`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      citations: []
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [selectedLang, setSelectedLang] = useState('en');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = async (queryText) => {
    const text = queryText || inputQuery;
    if (!text.trim()) return;

    const userMsg = {
      id: Date.now().toString(),
      sender: 'user',
      text: text.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setIsTyping(true);

    // Simulate Evidence-Grounded AI Response with Citations & Guardrails
    setTimeout(() => {
      let aiResponseText = '';
      let citations = [];

      const queryLower = text.toLowerCase();

      if (queryLower.includes('sugar') || queryLower.includes('hba1c') || queryLower.includes('glucose')) {
        if (selectedLang === 'ta') {
          aiResponseText = `உங்கள் பதிவேற்றப்பட்ட இரத்தப் பரிசோதனை ஆவணத்தின்படி:
• HbA1c அளவு: 7.2% (இயல்பு வரம்பு: < 5.7% - சற்று அதிகம்)
• Fasting Blood Sugar: 135 mg/dL (இயல்பு வரம்பு: 70 - 99 mg/dL)

உணவுமுறை ஆலோசனை:
வெள்ளை சர்க்கரை மற்றும் அதிக மாவுச்சத்து உள்ள உணவுகளைக் குறைக்கவும். கேழ்வரகு (Ragi), வெந்தயம் மற்றும் பாகற்காய் உணவில் சேர்த்துக் கொள்ளலாம். உங்கள் மருத்துவரை அணுகி ஆலோசிக்கவும்.`;
        } else if (selectedLang === 'tanglish') {
          aiResponseText = `Ungaloda uploaded blood test report padi:
• HbA1c Level: 7.2% (Normal range: < 5.7% - Konjam High)
• Fasting Blood Sugar: 135 mg/dL (Normal: 70 - 99 mg/dL)

Diet Suggestion:
White sugar kuraikkavum. Ragi, Pavakkai mattrum Vendhayam unavil serthukkollavum. Please consult your doctor for medical advice.`;
        } else {
          aiResponseText = `Based on your uploaded clinical laboratory records:
• HbA1c: 7.2% (Standard Reference: < 5.7% — Elevated / Diabetic range)
• Fasting Blood Glucose: 135 mg/dL (Standard Reference: 70 - 99 mg/dL)

Evidence-Based Dietary Guidance:
Incorporate low-glycemic index foods such as Finger Millet (Ragi), Bitter Gourd (Pavakkai), and Sprouted Moong Dal. Consult your diabetologist or physician for personal clinical management.`;
        }
        citations = [
          { docTitle: 'Annual Comprehensive Blood Panel.pdf', page: 1, text: 'HbA1c: 7.2 % [Ref: 4.0 - 5.6 %]' },
          { docTitle: 'Fasting Blood Sugar Test.pdf', page: 1, text: 'Glucose Fasting: 135 mg/dL [Ref: 70 - 99 mg/dL]' }
        ];
      } else if (queryLower.includes('medication') || queryLower.includes('prescription') || queryLower.includes('food timing')) {
        if (selectedLang === 'ta') {
          aiResponseText = `உங்கள் பரிந்துரைக்கப்பட்ட மருந்து விவரங்கள்:
• Metformin 500mg: காலை மற்றும் இரவு உணவுக்குப் பின் (PC) உட்கொள்ளவும்.
• Atorvastatin 10mg: இரவு உணவுக்குப் பின் (PC) உட்கொள்ளவும்.

மருத்துவர் அறிவுறுத்தியபடி மருந்துகளைத் தவறாமல் உட்கொள்ளவும்.`;
        } else if (selectedLang === 'tanglish') {
          aiResponseText = `Ungaloda active prescription details:
• Metformin 500mg: Morning & Night food-ku pinnaadi (PC) saapidavum.
• Atorvastatin 10mg: Night saappaattukku pinnaadi (PC) eduthukkollavum.`;
        } else {
          aiResponseText = `Extracted from your doctor's prescription records:
• Metformin 500 mg: Twice daily after meals (BD, PC)
• Atorvastatin 10 mg: Once daily at night after dinner (OD, PC)

Always verify pill instructions with your prescribing physician or pharmacist.`;
        }
        citations = [
          { docTitle: 'Physician Prescription - Dr. S. Ramanathan.pdf', page: 1, text: 'Rx: Tab Metformin 500mg 1-0-1 PC x 30 days' }
        ];
      } else {
        if (selectedLang === 'ta') {
          aiResponseText = `நான் உங்கள் மருத்துவ ஆவணங்களின் அடிப்படையில் மட்டுமே தகவல்களை வழங்குகிறேன். நீங்கள் கேட்கும் கேள்விக்கான போதுமான சான்றுகள் உங்கள் தற்போதைய ஆவணங்களில் இல்லை என்றால், தயவுசெய்து கூடுதல் அறிக்கைகளைப் பதிவேற்றவும் அல்லது உங்கள் மருத்துவரிடம் கேட்கவும்.`;
        } else if (selectedLang === 'tanglish') {
          aiResponseText = `Naan ungaloda uploaded medical records-il irukkum unmaiyaana thagavalgalai mattumey tharuven. Edheinum adhisayangal irundhal doctor-idam direct-aa kettukkollavum.`;
        } else {
          aiResponseText = `HealthMate AI operates strictly on evidence grounding. Every medical data point is verified against your uploaded files. If a detail is missing from your uploaded records, our Evidence Guard strictly prevents hallucinating values.`;
        }
        citations = [];
      }

      const aiMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: aiResponseText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations: citations
      };

      setMessages((prev) => [...prev, aiMsg]);
      setIsTyping(false);
    }, 700);
  };

  return (
    <div className="h-[calc(100vh-8.5rem)] flex flex-col space-y-4">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-extrabold text-slate-900 dark:text-white font-heading">
              Evidence-Grounded AI Clinical Assistant
            </h1>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-cyan-100 dark:bg-cyan-950 text-cyan-700 dark:text-cyan-300">
              Hybrid RAG
            </span>
          </div>
          <p className="text-xs text-slate-500">
            Answers strictly cited from your personal medical documents with zero hallucination tolerance
          </p>
        </div>

        {/* Trilingual Toggle */}
        <div className="flex items-center space-x-1 p-1 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 text-xs self-start sm:self-auto">
          <Languages className="w-3.5 h-3.5 text-brand-600 dark:text-brand-400 ml-1.5" />
          <button
            onClick={() => setSelectedLang('en')}
            className={`px-2 py-0.5 rounded-lg font-medium ${
              selectedLang === 'en' ? 'bg-brand-600 text-white' : 'text-slate-500'
            }`}
          >
            English
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
      </div>

      {/* Non-Diagnostic Disclaimer Banner */}
      <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 text-xs text-amber-800 dark:text-amber-300 flex items-center space-x-2 shrink-0">
        <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600" />
        <span>
          <strong>Clinical Disclaimer:</strong> HealthMate AI provides informational summaries from your uploaded records. AI does not diagnose or prescribe. Consult a licensed doctor for medical care.
        </span>
      </div>

      {/* Chat Messages Area */}
      <div className="flex-1 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 overflow-y-auto space-y-4 shadow-sm">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start space-x-3 ${msg.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}
          >
            <div
              className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
                msg.sender === 'user'
                  ? 'bg-brand-600 text-white'
                  : 'bg-gradient-to-tr from-cyan-600 to-teal-500 text-white'
              }`}
            >
              {msg.sender === 'user' ? <User className="w-4 h-4" /> : <BotMessageSquare className="w-4 h-4" />}
            </div>

            <div className={`space-y-2 max-w-xl ${msg.sender === 'user' ? 'text-right' : 'text-left'}`}>
              <div
                className={`p-3.5 rounded-2xl text-xs leading-relaxed ${
                  msg.sender === 'user'
                    ? 'bg-brand-600 text-white rounded-tr-none'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-tl-none whitespace-pre-wrap'
                }`}
              >
                {msg.text}
              </div>

              {/* Source Document Citations (Evidence Grounding) */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-left space-y-1.5">
                  <div className="flex items-center space-x-1 text-[10px] font-bold uppercase text-brand-600 dark:text-brand-400">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>Verified Source Citations</span>
                  </div>
                  {msg.citations.map((c, i) => (
                    <div key={i} className="text-[11px] text-slate-600 dark:text-slate-300 flex items-start space-x-1.5">
                      <FileText className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-semibold text-slate-800 dark:text-slate-200">
                          {c.docTitle} (p. {c.page})
                        </span>
                        <p className="text-[10px] text-slate-500 italic">"{c.text}"</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <span className="text-[10px] text-slate-400 block px-1">{msg.timestamp}</span>
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex items-center space-x-2 text-slate-400 text-xs p-2">
            <BotMessageSquare className="w-4 h-4 text-brand-500 animate-pulse" />
            <span>Scanning uploaded records & grounding evidence...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Clinical Prompts */}
      <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 shrink-0">
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider whitespace-nowrap pl-1">
          Suggestions:
        </span>
        {SUGGESTED_PROMPTS.map((prompt, index) => (
          <button
            key={index}
            onClick={() => handleSend(prompt)}
            className="px-2.5 py-1 rounded-lg text-[11px] bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-brand-400 dark:hover:border-brand-600 text-slate-600 dark:text-slate-300 whitespace-nowrap transition-colors"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Query Input Box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex items-center space-x-2 shrink-0"
      >
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          placeholder={`Ask about your blood tests, active medicines, or dietary advice (${selectedLang.toUpperCase()})...`}
          className="flex-1 px-4 py-2.5 text-xs rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500 text-slate-900 dark:text-white"
        />
        <button
          type="submit"
          disabled={!inputQuery.trim() || isTyping}
          className="p-2.5 bg-gradient-to-r from-brand-600 to-cyan-600 hover:from-brand-700 hover:to-cyan-700 disabled:opacity-50 text-white rounded-xl shadow-md transition-all active:scale-95"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};

export default AIAssistantPage;
