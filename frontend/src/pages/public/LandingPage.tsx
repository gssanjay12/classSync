import React from 'react';
import { Link } from 'react-router-dom';
import {
  Vote,
  Share2,
  CheckCircle2,
  Users,
  ShieldCheck,
  BarChart3,
  ArrowRight,
  Sparkles,
  Smartphone,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Top Navbar */}
      <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b border-slate-200/80">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center font-bold shadow-md shadow-indigo-200">
              CP
            </div>
            <div>
              <span className="text-xl font-extrabold text-slate-900 tracking-tight">ClassPoll</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/login"
              className="px-5 py-2.5 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-sm shadow-indigo-200 transition-all active:scale-95"
            >
              Sign In
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-16 pb-24 md:pt-24 md:pb-32">
        <div className="max-w-5xl mx-auto px-6 text-center">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs font-semibold mb-6">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Class-Based Poll Participation & Tracking</span>
          </div>

          <h1 className="text-4xl md:text-6xl font-black text-slate-900 tracking-tight leading-[1.15] mb-6">
            Create. Share. <span className="text-indigo-600">Track.</span>
          </h1>

          <p className="text-lg md:text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed mb-10">
            Create verified class polls, share them seamlessly through WhatsApp, and instantly know who has responded and who is still pending.
          </p>

          <div className="flex items-center justify-center">
            <Link
              to="/login"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 text-base font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-xl shadow-lg shadow-indigo-200 transition-all active:scale-95"
            >
              <span>Access Institutional Portal</span>
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>

          {/* Value comparison pill */}
          <div className="mt-12 inline-flex items-center gap-3 px-5 py-2.5 rounded-2xl bg-white border border-slate-200/80 shadow-xs text-xs font-medium text-slate-600">
            <span className="flex items-center gap-1.5 text-emerald-600 font-semibold">
              <Smartphone className="w-4 h-4" /> WhatsApp = Distribution
            </span>
            <span className="text-slate-300">|</span>
            <span className="flex items-center gap-1.5 text-indigo-600 font-semibold">
              <CheckCircle2 className="w-4 h-4" /> ClassPoll = System of Record
            </span>
          </div>
        </div>
      </section>

      {/* Feature Grid */}
      <section className="py-20 bg-white border-y border-slate-200/70">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl font-bold text-slate-900 tracking-tight mb-3">
              Purpose-built for Colleges & Classrooms
            </h2>
            <p className="text-slate-500 text-sm md:text-base">
              Say goodbye to messy WhatsApp message roll calls and manual tallying.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-100 hover:border-indigo-100 transition-all">
              <div className="w-12 h-12 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center mb-5">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">Automated DONE / NOT DONE</h3>
              <p className="text-slate-600 text-sm leading-relaxed">
                When a student answers, they instantly shift to DONE. Teachers see pending students in real time with register numbers.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-100 hover:border-indigo-100 transition-all">
              <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center mb-5">
                <Share2 className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">One-Click WhatsApp Sharing</h3>
              <p className="text-slate-600 text-sm leading-relaxed">
                Generates a secure deep link with pre-filled question details ready to post straight into your WhatsApp group.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-50 border border-slate-100 hover:border-indigo-100 transition-all">
              <div className="w-12 h-12 rounded-xl bg-purple-100 text-purple-600 flex items-center justify-center mb-5">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">Class Isolation & RBAC</h3>
              <p className="text-slate-600 text-sm leading-relaxed">
                Strict membership verification. Students from AIDS-B can never view or answer polls meant for AIDS-A.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto py-8 bg-slate-50 text-center text-xs text-slate-400">
        <p>© 2026 ClassPoll. Built with FastAPI, PostgreSQL & React.</p>
      </footer>
    </div>
  );
};
