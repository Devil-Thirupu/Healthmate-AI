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
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col selection:bg-brand-500 selection:text-white">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-white/80 dark:bg-slate-900/80 backdrop-blur border-b border-slate-200 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-cyan-400 flex items-center justify-center text-white shadow-md shadow-brand-500/20">
              <Activity className="w-5 h-5" />
            </div>
            <span className="font-heading font-bold text-xl tracking-tight text-slate-900 dark:text-white">
              HEALTHMATE <span className="text-brand-600 dark:text-brand-400">AI</span>
            </span>
          </div>

          <div className="flex items-center space-x-3">
            <Link
              to="/login"
              className="px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:text-brand-600 dark:hover:text-brand-400 transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/register"
              className="px-4 py-2 bg-gradient-to-r from-brand-600 to-cyan-600 hover:from-brand-700 hover:to-cyan-700 text-white text-xs font-semibold rounded-xl shadow-md shadow-brand-500/20 transition-all active:scale-95"
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
            <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-brand-50 dark:bg-brand-950/60 border border-brand-200 dark:border-brand-800 text-brand-700 dark:text-brand-300 text-xs font-medium">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Intelligent Personal Health Record & Medical Document Assistant</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 dark:text-white tracking-tight leading-tight">
              Your Medical Records,{' '}
              <span className="bg-gradient-to-r from-brand-600 via-cyan-500 to-teal-400 bg-clip-text text-transparent">
                Digitized, Explained & Protected
              </span>
            </h1>

            <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
              HealthMate AI unifies your prescriptions, blood tests, and medical summaries into a secure, SHA-256 verified personal health vault with evidence-grounded AI insights in <strong>English, Tamil, and Tanglish</strong>.
            </p>

            <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link
                to="/register"
                className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-3.5 bg-gradient-to-r from-brand-600 to-cyan-600 hover:from-brand-700 hover:to-cyan-700 text-white text-sm font-semibold rounded-xl shadow-lg shadow-brand-500/25 transition-all active:scale-95"
              >
                <span>Create Patient Account</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/login"
                className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/50 text-slate-700 dark:text-slate-200 text-sm font-semibold rounded-xl transition-colors"
              >
                Sign In to Vault
              </Link>
            </div>

            {/* Trust Highlights */}
            <div className="pt-10 grid grid-cols-2 md:grid-cols-4 gap-4 text-left">
              <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 shadow-sm">
                <ShieldCheck className="w-5 h-5 text-emerald-500 mb-2" />
                <h4 className="text-xs font-bold text-slate-900 dark:text-white">SHA-256 Integrity</h4>
                <p className="text-[11px] text-slate-500 mt-0.5">Cryptographic checksums for every uploaded record</p>
              </div>

              <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 shadow-sm">
                <FileSearch className="w-5 h-5 text-cyan-500 mb-2" />
                <h4 className="text-xs font-bold text-slate-900 dark:text-white">Multi-Tier OCR</h4>
                <p className="text-[11px] text-slate-500 mt-0.5">Automated extraction of lab tests & medications</p>
              </div>

              <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 shadow-sm">
                <Languages className="w-5 h-5 text-brand-500 mb-2" />
                <h4 className="text-xs font-bold text-slate-900 dark:text-white">Trilingual Guidance</h4>
                <p className="text-[11px] text-slate-500 mt-0.5">Medical advice in English, தமிழ், & Tanglish</p>
              </div>

              <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 shadow-sm">
                <Lock className="w-5 h-5 text-amber-500 mb-2" />
                <h4 className="text-xs font-bold text-slate-900 dark:text-white">PIN-Controlled Sharing</h4>
                <p className="text-[11px] text-slate-500 mt-0.5">Temporary access links with automatic expiry</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Showcase */}
      <section className="py-16 bg-white dark:bg-slate-900/50 border-y border-slate-200 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white font-heading">
              A Complete Clinical-Grade Health Hub
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 mt-2">
              Engineered with strict clinical evidence guardrails, zero hallucination tolerance, and patient data privacy.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 space-y-3">
              <div className="w-10 h-10 rounded-xl bg-brand-100 dark:bg-brand-950 text-brand-600 dark:text-brand-400 flex items-center justify-center">
                <FlaskConical className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Lab Reports & Biomarkers</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Automatically extract biomarkers (HbA1c, Cholesterol, Hemoglobin, Creatinine) with normal reference ranges and abnormal flag alerts.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 space-y-3">
              <div className="w-10 h-10 rounded-xl bg-teal-100 dark:bg-teal-950 text-teal-600 dark:text-teal-400 flex items-center justify-center">
                <Pill className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Prescription Clarifier</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Converts complex doctor shorthand (OD, BD, TID, AC, PC) into plain-language dosage instructions and meal timings in Tamil and Tanglish.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 space-y-3">
              <div className="w-10 h-10 rounded-xl bg-cyan-100 dark:bg-cyan-950 text-cyan-600 dark:text-cyan-400 flex items-center justify-center">
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
      <footer className="mt-auto py-8 bg-slate-100 dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© 2026 HEALTHMATE AI — All Rights Reserved. Personal Health Record System.</p>
          <div className="flex items-center space-x-4">
            <span className="text-[11px] text-amber-600 dark:text-amber-400">
              * Non-Diagnostic Informational Assistant
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
