import React from 'react';
import { ShieldCheck, ListOrdered, FileText, BarChart3, Database, AlertCircle } from 'lucide-react';
import type { HealthResponse } from '../types';

interface NavbarProps {
  currentTab: 'queue' | 'case' | 'benchmark';
  setCurrentTab: (tab: 'queue' | 'case' | 'benchmark') => void;
  activeCaseId: string | null;
  health: HealthResponse | null;
  onSeed: () => void;
  isSeeding: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  setCurrentTab,
  activeCaseId,
  health,
  onSeed,
  isSeeding,
}) => {
  const isAiUnavailable = health && (health.llm_status !== 'ok' || health.demo_mode);

  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-40">
      {/* AI Unavailable Banner */}
      {isAiUnavailable && (
        <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-1.5 text-xs text-amber-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-400" />
            <span>
              <strong>AI Fallback Mode Active:</strong> LLM is offline or in demo mode ({health?.llm_provider || 'mock'}). Using deterministic rule-based extractions and verified templates.
            </span>
          </div>
          <span className="text-[10px] uppercase font-mono tracking-wider bg-amber-500/20 px-2 py-0.5 rounded text-amber-200">
            Guaranteed Offline Demo
          </span>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => setCurrentTab('queue')}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20 border border-blue-400/30">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg text-white tracking-tight">ProofPilot</span>
              <span className="text-[10px] uppercase font-mono bg-blue-500/20 text-blue-300 border border-blue-500/30 px-1.5 py-0.5 rounded">
                Dispute AI
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Grounding Verifier & Economics Engine</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-slate-900/60 p-1 rounded-xl border border-slate-800/80">
          <button
            onClick={() => setCurrentTab('queue')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              currentTab === 'queue'
                ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <ListOrdered className="w-4 h-4" />
            Triage Queue
          </button>

          <button
            onClick={() => setCurrentTab('case')}
            disabled={!activeCaseId}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              currentTab === 'case'
                ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                : activeCaseId
                ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                : 'text-slate-600 cursor-not-allowed opacity-50'
            }`}
          >
            <FileText className="w-4 h-4" />
            Case Workspace {activeCaseId && <span className="text-[10px] opacity-75 font-mono">({activeCaseId})</span>}
          </button>

          <button
            onClick={() => setCurrentTab('benchmark')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
              currentTab === 'benchmark'
                ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            Benchmark & Evaluation
          </button>
        </nav>

        {/* Status Badges & Seed Action */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 text-xs font-mono">
            <span className="flex items-center gap-1.5 px-2 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300">
              <span className={`w-2 h-2 rounded-full ${health?.llm_status === 'ok' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
              {health?.llm_provider || 'mock'}
            </span>
          </div>

          <button
            onClick={onSeed}
            disabled={isSeeding}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-200 transition-all shadow-sm disabled:opacity-50"
            title="Seed 50 synthetic test cases"
          >
            <Database className={`w-3.5 h-3.5 ${isSeeding ? 'animate-spin text-blue-400' : 'text-slate-400'}`} />
            <span>{isSeeding ? 'Seeding...' : 'Seed Data'}</span>
          </button>
        </div>
      </div>
    </header>
  );
};
