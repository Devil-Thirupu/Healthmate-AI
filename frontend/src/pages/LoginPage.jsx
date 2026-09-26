import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Activity,
  Lock,
  Mail,
  Phone,
  AlertCircle,
  Loader2,
  Sparkles,
  ShieldCheck,
  FileText,
  Cpu,
  CheckCircle2,
  ArrowRight
} from 'lucide-react';

const LoginPage = () => {
  const [loginMethod, setLoginMethod] = useState('mobile'); // 'mobile' or 'email'
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState('');
  const [googleNotice, setGoogleNotice] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login, loginMobile, loginGoogle, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/dashboard';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setGoogleNotice('');
    setIsLoading(true);

    try {
      if (loginMethod === 'mobile') {
        await loginMobile(identifier, password);
      } else {
        await login(identifier, password);
      }
      navigate(from, { replace: true });
    } catch (err) {
      console.error('Login failed:', err);
      setError(err.response?.data?.detail || 'Invalid credentials. Please verify your phone/email and password.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setError('');
    setGoogleNotice('');
    setIsLoading(true);
    try {
      await loginGoogle('simulated_or_google_token_placeholder');
      navigate(from, { replace: true });
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (detail && detail.includes('Google Sign-In is not configured')) {
        setGoogleNotice('Google Sign-In is not configured.');
      } else if (detail) {
        setGoogleNotice(detail);
      } else {
        setGoogleNotice('Google Sign-In is not configured.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setError('');
    setGoogleNotice('');
    setIsLoading(true);
    const demoEmail = 'patient.demo@healthmate.ai';
    const demoPassword = 'DemoPatient2026!';

    try {
      await login(demoEmail, demoPassword);
      navigate(from, { replace: true });
    } catch (err) {
      try {
        await register({
          email: demoEmail,
          password: demoPassword,
          full_name: 'Dr. Anand Ramanathan (Demo Patient)',
          phone_number: '+919876543210',
          role: 'patient',
          date_of_birth: '1985-06-12',
          gender: 'Male',
          blood_group: 'B+',
          allergies: 'Penicillin, Dust mites',
          chronic_conditions: 'Mild Hypertension',
          language_preference: 'ta'
        });
        navigate(from, { replace: true });
      } catch (regErr) {
        setError('Could not initialize demo session. Please register manually.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] dark:bg-slate-950 flex">
      {/* Left Clinical Branding Panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-[#094d44] via-[#0d5c52] to-[#083b34] text-white p-12 flex-col justify-between relative overflow-hidden">
        {/* Background Ambient Glow */}
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-teal-400/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-emerald-400/10 rounded-full blur-3xl pointer-events-none" />

        {/* Brand Top Header */}
        <div className="relative z-10">
          <div className="flex items-center space-x-3">
            <div className="w-11 h-11 rounded-xl bg-teal-500/20 border border-teal-400/30 flex items-center justify-center text-teal-300 backdrop-blur-md shadow-lg shadow-teal-950/40">
              <Activity className="w-6 h-6 text-teal-300 animate-pulse" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight font-heading flex items-center space-x-2">
                <span>HEALTHMATE</span>
                <span className="text-xs px-2 py-0.5 rounded-md bg-teal-400/20 text-teal-200 border border-teal-300/30 font-semibold tracking-wider uppercase">
                  AI CLINICAL
                </span>
              </h1>
              <p className="text-[11px] text-teal-200/70 font-medium tracking-wide">
                INTELLIGENT MEDICAL RECORD SYNTHESIS & VAULT
              </p>
            </div>
          </div>
        </div>

        {/* Feature Highlights Center */}
        <div className="relative z-10 my-auto py-8 space-y-6 max-w-lg">
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-400/10 border border-teal-300/20 text-teal-200 text-xs font-medium mb-4">
              <ShieldCheck className="w-3.5 h-3.5 text-teal-300" />
              <span>Evidence-Grounded Clinical Decision Support</span>
            </div>
            <h2 className="text-3xl font-extrabold text-white tracking-tight leading-tight font-heading">
              Secure patient health records with clinical-grade AI intelligence.
            </h2>
            <p className="mt-3 text-sm text-teal-100/80 leading-relaxed font-sans">
              Seamlessly analyze laboratory diagnostics, track historical biomarkers, review prescription safety, and prep for doctor visits with grounded citations.
            </p>
          </div>

          <div className="grid grid-cols-1 gap-3.5 pt-2">
            {[
              {
                icon: FileText,
                title: 'Automated Lab & Prescription OCR',
                desc: 'Instant structured extraction from medical PDFs and images with strict verification.',
              },
              {
                icon: ShieldCheck,
                title: 'Evidence Guard & Citation Engine',
                desc: 'Zero-hallucination answers backed by verifiable source document snippets.',
              },
              {
                icon: Cpu,
                title: 'Trilingual Clinical Copilot',
                desc: 'Accessible medical summaries in English, தமிழ் (Tamil), and Multilanguage.',
              },
            ].map((feature, idx) => {
              const Icon = feature.icon;
              return (
                <div
                  key={idx}
                  className="flex items-start space-x-3.5 p-3.5 rounded-xl bg-white/5 border border-white/10 backdrop-blur-xs hover:bg-white/10 transition-colors"
                >
                  <div className="p-2 rounded-lg bg-teal-400/20 text-teal-200 shrink-0 mt-0.5">
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-semibold text-white">{feature.title}</h3>
                    <p className="text-[11px] text-teal-100/70 mt-0.5">{feature.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Bottom Security Footer */}
        <div className="relative z-10 flex items-center justify-between text-[11px] text-teal-200/60 border-t border-white/10 pt-4">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
            <span>End-to-End Encrypted Medical Records</span>
          </div>
          <span>v2.6.4 Clinical Engine</span>
        </div>
      </div>

      {/* Right Login Form Panel */}
      <div className="flex-1 flex flex-col justify-center px-4 sm:px-8 lg:px-16 xl:px-24 py-12">
        <div className="w-full max-w-md mx-auto">
          {/* Mobile Header (Shown on Small Screens) */}
          <div className="lg:hidden text-center mb-8">
            <div className="w-12 h-12 rounded-2xl bg-teal-600 flex items-center justify-center text-white shadow-md shadow-teal-700/20 mx-auto">
              <Activity className="w-7 h-7" />
            </div>
            <h2 className="mt-3 text-2xl font-extrabold text-slate-900 dark:text-white font-heading">
              HEALTHMATE AI
            </h2>
            <p className="text-xs text-slate-500">Clinical Intelligence & Medical Record Portal</p>
          </div>

          {/* Card Container */}
          <div className="bg-white dark:bg-slate-900 p-8 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-sm">
            <div className="mb-6">
              <span className="text-[10px] font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-950/60 px-2.5 py-1 rounded-full border border-teal-200/50 dark:border-teal-800/40">
                Authorized Access
              </span>
              <h2 className="text-2xl font-bold text-slate-900 dark:text-white mt-2 font-heading">
                Sign in to your Vault
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Enter your registered credentials to access clinical records.
              </p>
            </div>

            {error && (
              <div className="mb-4 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-900 text-rose-700 dark:text-rose-300 text-xs flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {googleNotice && (
              <div className="mb-4 p-3 rounded-xl bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-900 text-amber-700 dark:text-amber-300 text-xs flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{googleNotice}</span>
              </div>
            )}

            {/* Login Method Pill Tabs */}
            <div className="flex p-1 bg-slate-100 dark:bg-slate-800/80 rounded-xl text-xs font-semibold mb-5">
              <button
                type="button"
                onClick={() => {
                  setLoginMethod('mobile');
                  setError('');
                }}
                className={`flex-1 py-2 rounded-lg transition-all flex items-center justify-center space-x-1.5 ${
                  loginMethod === 'mobile'
                    ? 'bg-white dark:bg-slate-900 text-teal-700 dark:text-teal-300 shadow-xs font-bold'
                    : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 font-medium'
                }`}
              >
                <Phone className="w-3.5 h-3.5" />
                <span>Mobile Number</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  setLoginMethod('email');
                  setError('');
                }}
                className={`flex-1 py-2 rounded-lg transition-all flex items-center justify-center space-x-1.5 ${
                  loginMethod === 'email'
                    ? 'bg-white dark:bg-slate-900 text-teal-700 dark:text-teal-300 shadow-xs font-bold'
                    : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 font-medium'
                }`}
              >
                <Mail className="w-3.5 h-3.5" />
                <span>Email Address</span>
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  {loginMethod === 'mobile' ? 'Mobile Phone Number' : 'Clinical / Patient Email'}
                </label>
                <div className="relative">
                  {loginMethod === 'mobile' ? (
                    <Phone className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  ) : (
                    <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  )}
                  <input
                    type={loginMethod === 'mobile' ? 'tel' : 'email'}
                    required
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    placeholder={loginMethod === 'mobile' ? '+91 98765 43210' : 'patient@example.com'}
                    className="w-full pl-10 pr-3.5 py-2.5 text-xs rounded-xl bg-slate-50/70 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-600 text-slate-900 dark:text-white transition-colors"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Vault Password
                  </label>
                  <a
                    href="#forgot"
                    onClick={(e) => {
                      e.preventDefault();
                      alert('To reset your password, please contact your clinic administrator or register with a new demo account.');
                    }}
                    className="text-[11px] font-medium text-teal-600 hover:text-teal-700 dark:text-teal-400"
                  >
                    Forgot password?
                  </a>
                </div>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full pl-10 pr-3.5 py-2.5 text-xs rounded-xl bg-slate-50/70 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-600 text-slate-900 dark:text-white transition-colors"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between pt-1">
                <label className="flex items-center space-x-2 text-xs text-slate-600 dark:text-slate-400 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-3.5 h-3.5 text-teal-600 rounded border-slate-300 focus:ring-teal-500"
                  />
                  <span>Keep session active on this workstation</span>
                </label>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-2.5 px-4 bg-teal-600 hover:bg-teal-700 active:bg-teal-800 text-white text-xs font-bold rounded-xl shadow-sm transition-all flex items-center justify-center space-x-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Authenticating Vault...</span>
                  </>
                ) : (
                  <>
                    <span>Sign In to Vault</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </form>

            {/* Divider */}
            <div className="relative flex py-3 items-center">
              <div className="flex-grow border-t border-slate-200 dark:border-slate-800"></div>
              <span className="flex-shrink mx-3 text-[11px] text-slate-400 uppercase tracking-wider font-semibold">
                Or Continue With
              </span>
              <div className="flex-grow border-t border-slate-200 dark:border-slate-800"></div>
            </div>

            {/* Google Sign-In */}
            <button
              type="button"
              onClick={handleGoogleLogin}
              disabled={isLoading}
              className="w-full py-2 px-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 text-xs font-semibold hover:bg-slate-50 dark:hover:bg-slate-750 transition-colors flex items-center justify-center space-x-2 shadow-xs"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"
                />
                <path
                  fill="#34A853"
                  d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 10.03 0 12s.45 3.82 1.25 5.42l4.03-3.15z"
                />
                <path
                  fill="#EA4335"
                  d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
                />
              </svg>
              <span>Single Sign-On with Google</span>
            </button>

            {/* Quick Demo Access */}
            <div className="pt-3">
              <button
                type="button"
                onClick={handleDemoLogin}
                disabled={isLoading}
                className="w-full py-2 px-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200/80 dark:border-emerald-800/60 text-emerald-800 dark:text-emerald-300 text-xs font-bold hover:bg-emerald-100 dark:hover:bg-emerald-900/40 transition-colors flex items-center justify-center space-x-1.5 shadow-xs"
              >
                <Sparkles className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                <span>Instant Demo Account (One Click)</span>
              </button>
            </div>

            <div className="text-center pt-5 border-t border-slate-100 dark:border-slate-800/80 mt-5">
              <p className="text-xs text-slate-500">
                Need a new patient or doctor account?{' '}
                <Link to="/register" className="font-bold text-teal-600 hover:text-teal-700 dark:text-teal-400">
                  Register Vault
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
