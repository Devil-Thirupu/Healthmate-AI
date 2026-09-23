import React from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  ShieldCheck,
  Languages,
  FileSearch,
  Pill,
  FlaskConical,
  Lock,
  ArrowRight,
  CheckCircle2,
  Sparkles,
  BotMessageSquare,
  FileCheck
} from 'lucide-react';

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col selection:bg-teal-500 selection:text-white">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-teal-600 flex items-center justify-center text-white shadow-xs">
              <Activity className="w-5 h-5 text-teal-100" />
            </div>
            <div className="flex flex-col">
              <span className="font-heading font-black text-lg tracking-tight text-slate-900 dark:text-white leading-none">
                HEALTHMATE <span className="text-teal-600 dark:text-teal-400">AI</span>
              </span>
              <span className="text-[10px] font-bold text-slate-400 tracking-wider uppercase">Clinical Intelligence</span>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <Link
              to="/login"
              className="px-4 py-2 text-xs font-bold text-slate-700 dark:text-slate-200 hover:text-teal-600 dark:hover:text-teal-400 transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/register"
              className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl shadow-xs transition-all active:scale-95"
            >
              Get Started Free
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-20 lg:pt-20 lg:pb-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto space-y-6">
            <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-teal-50 dark:bg-teal-950/60 border border-teal-200/80 dark:border-teal-800 text-teal-800 dark:text-teal-300 text-xs font-bold">
              <Sparkles className="w-3.5 h-3.5 text-teal-600" />
              <span>Intelligent Personal Health Record & Medical Document Assistant</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-slate-900 dark:text-white tracking-tight leading-tight">
              Your Medical Records,{' '}
              <span className="bg-gradient-to-r from-teal-600 via-teal-500 to-emerald-500 bg-clip-text text-transparent">
                Digitized, Explained & Protected
              </span>
            </h1>

            <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed font-normal">
              HealthMate AI unifies your prescriptions, blood tests, and medical summaries into a secure, SHA-256 verified personal health vault with evidence-grounded AI insights in <strong>English, Tamil, and Tanglish</strong>.
            </p>

            <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link
                to="/register"
                className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-3.5 bg-teal-600 hover:bg-teal-700 text-white text-sm font-bold rounded-xl shadow-md shadow-teal-700/20 transition-all active:scale-95 cursor-pointer"
              >
                <span>Create Patient Account</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/login"
                className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/50 text-slate-700 dark:text-slate-200 text-sm font-bold rounded-xl transition-colors cursor-pointer"
              >
                Sign In to Vault
              </Link>
            </div>

            {/* Trust Highlights */}
            <div className="pt-10 grid grid-cols-2 md:grid-cols-4 gap-4 text-left">
              <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs">
                <ShieldCheck className="w-5 h-5 text-emerald-600 mb-2" />
                <h4 className="text-xs font-bold text-slate-900 dark:text-white">SHA-256 Integrity</h4>
                <p className="text-[11px] text-slate-500 mt-0.5">Cryptographic checksums for every uploaded record</p>
              </div>

              <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs">
                <FileSearch className="w-5 h-5 text-teal-600 mb-2" />
                <h4 className="text-xs font-bold text-slate-900 dark:text-white">Multi-Tier OCR</h4>
                <p className="text-[11px] text-slate-500 mt-0.5">Automated extraction of lab tests & medications</p>
              </div>

              <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs">
                <Languages className="w-5 h-5 text-teal-700 mb-2" />
                <h4 className="text-xs font-bold text-slate-900 dark:text-white">Trilingual Guidance</h4>
                <p className="text-[11px] text-slate-500 mt-0.5">Medical advice in English, தமிழ், & Tanglish</p>
              </div>

              <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs">
                <Lock className="w-5 h-5 text-amber-600 mb-2" />
                <h4 className="text-xs font-bold text-slate-900 dark:text-white">PIN-Controlled Sharing</h4>
                <p className="text-[11px] text-slate-500 mt-0.5">Temporary access links with automatic expiry</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Showcase */}
      <section className="py-16 bg-white dark:bg-slate-900/50 border-y border-slate-200/90 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white tracking-tight">
              A Complete Clinical-Grade Health Hub
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 mt-2">
              Engineered with strict clinical evidence guardrails, zero hallucination tolerance, and patient data privacy.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 space-y-3">
              <div className="w-10 h-10 rounded-xl bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-400 flex items-center justify-center">
                <FlaskConical className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Lab Reports & Biomarkers</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Automatically extract biomarkers (HbA1c, Cholesterol, Hemoglobin, Creatinine) with normal reference ranges and abnormal flag alerts.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 space-y-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-400 flex items-center justify-center">
                <Pill className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Prescription Clarifier</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Converts complex doctor shorthand (OD, BD, TID, AC, PC) into plain-language dosage instructions and meal timings in Tamil and Tanglish.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 space-y-3">
              <div className="w-10 h-10 rounded-xl bg-sky-50 dark:bg-sky-950 text-sky-700 dark:text-sky-400 flex items-center justify-center">
                <BotMessageSquare className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Evidence-Grounded RAG AI</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Ask questions about your medical history with clickable source document citations and strict rejection of ungrounded medical claims.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto py-8 bg-slate-100 dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800 text-center text-xs text-slate-500 font-medium">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© 2026 HEALTHMATE AI — All Rights Reserved. Personal Health Record System.</p>
          <div className="flex items-center space-x-4">
            <span className="text-[11px] text-amber-600 dark:text-amber-400 font-semibold">
              * Non-Diagnostic Informational Assistant
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
