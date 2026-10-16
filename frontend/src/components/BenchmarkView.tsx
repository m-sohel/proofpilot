import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingUp,
  ShieldCheck,
  Target,
  Info,
  CheckCircle2,
  AlertCircle,
  Play,
} from 'lucide-react';
import type { BenchmarkMetrics } from '../types';
import { api } from '../api';

export const BenchmarkView: React.FC = () => {
  const [metrics, setMetrics] = useState<BenchmarkMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [useAllCases, setUseAllCases] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runBenchmark = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getBenchmark(useAllCases);
      setMetrics(data);
    } catch (err: any) {
      setError(err.message || 'Failed to run benchmark');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runBenchmark();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [useAllCases]);

  const valueAddedVsContest = metrics
    ? metrics.proofpilot_net_return - metrics.contest_all_net_return
    : 0;
  const valueAddedVsConcede = metrics
    ? metrics.proofpilot_net_return - metrics.concede_all_net_return
    : 0;

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="glass-panel rounded-2xl p-5 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-blue-400" />
            <h1 className="text-lg font-bold text-white tracking-tight">Benchmark & Evaluation Suite</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Empirical evaluation against ground-truth synthetic labels and financial baselines.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 p-1 rounded-xl text-xs">
            <button
              onClick={() => setUseAllCases(false)}
              className={`px-3 py-1 rounded-lg transition-colors font-medium ${
                !useAllCases
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Test Split (20% Holdout)
            </button>
            <button
              onClick={() => setUseAllCases(true)}
              className={`px-3 py-1 rounded-lg transition-colors font-medium ${
                useAllCases
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              All 50 Cases
            </button>
          </div>

          <button
            onClick={runBenchmark}
            disabled={loading}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-white transition-colors disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-400' : 'text-blue-400'}`} />
            <span>{loading ? 'Evaluating...' : 'Re-Run Benchmark'}</span>
          </button>
        </div>
      </div>

      {/* Synthetic Data Disclaimer Alert */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3 text-xs text-slate-400 flex items-start gap-2.5">
        <Info className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong>Notice:</strong> All benchmark metrics and financial returns displayed below are derived from 
          reproducible synthetic dispute data and a transparent simulation model. They demonstrate system accuracy 
          and deterministic economics, but are <em>not evidence of real-world financial performance</em>.
        </p>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-3 text-xs text-rose-300">
          {error}
        </div>
      )}

      {loading ? (
        <div className="glass-panel rounded-2xl p-16 text-center border border-slate-800">
          <div className="inline-flex items-center gap-2 text-slate-400 text-sm">
            <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            Running benchmark evaluation across dispute test split...
          </div>
        </div>
      ) : metrics ? (
        <>
          {/* Key Accuracy & Verifier Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="glass-panel rounded-2xl p-4 border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Extraction Accuracy</span>
                <Target className="w-4 h-4 text-blue-400" />
              </div>
              <div className="mt-2 text-2xl font-bold text-white font-mono">
                {(metrics.extraction_accuracy * 100).toFixed(1)}%
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
                <div
                  className="bg-blue-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${metrics.extraction_accuracy * 100}%` }}
                />
              </div>
              <span className="text-[10px] text-slate-500 mt-1 block">Expected vs extracted fact types</span>
            </div>

            <div className="glass-panel rounded-2xl p-4 border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Contradiction Detection</span>
                <ShieldCheck className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="mt-2 text-2xl font-bold text-white font-mono">
                {(metrics.contradiction_recall * 100).toFixed(1)}%
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
                <div
                  className="bg-indigo-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${metrics.contradiction_recall * 100}%` }}
                />
              </div>
              <span className="text-[10px] text-slate-500 mt-1 block">
                Recall: {(metrics.contradiction_recall * 100).toFixed(0)}% • Prec: {(metrics.contradiction_precision * 100).toFixed(0)}%
              </span>
            </div>

            <div className="glass-panel rounded-2xl p-4 border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Grounding Rate</span>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="mt-2 text-2xl font-bold text-emerald-400 font-mono">
                {(metrics.grounding_rate * 100).toFixed(1)}%
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
                <div
                  className="bg-emerald-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${metrics.grounding_rate * 100}%` }}
                />
              </div>
              <span className="text-[10px] text-slate-500 mt-1 block">Verified sentences with valid citations</span>
            </div>

            <div className="glass-panel rounded-2xl p-4 border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Hallucinated Entities</span>
                <AlertCircle className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="mt-2 text-2xl font-bold text-emerald-400 font-mono">
                {metrics.hallucinated_count}
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
                <div className="bg-emerald-500 h-full rounded-full" style={{ width: '100%' }} />
              </div>
              <span className="text-[10px] text-slate-500 mt-1 block">Fabricated dates/amounts/IDs (Target: 0)</span>
            </div>
          </div>

          {/* Economics Comparison Card vs Baselines */}
          <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-emerald-400" />
                  Net Economics vs Dispute Baselines
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  ProofPilot economics filter out negative expected-value disputes and fatal contradictions.
                </p>
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                <div className="px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-xs">
                  <span className="text-slate-400">vs Contest All:</span>{' '}
                  <strong className="text-emerald-400 font-mono">+${valueAddedVsContest.toFixed(2)}</strong>
                </div>
                <div className="px-3 py-1.5 rounded-xl bg-blue-500/10 border border-blue-500/30 text-xs">
                  <span className="text-slate-400">vs Concede All:</span>{' '}
                  <strong className="text-blue-400 font-mono">+${valueAddedVsConcede.toFixed(2)}</strong>
                </div>
              </div>
            </div>

            {/* Visual Comparative Bars */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* ProofPilot */}
              <div className="bg-slate-900/80 p-4 rounded-xl border border-blue-500/30 relative overflow-hidden">
                <div className="absolute top-0 right-0 bg-blue-600 text-[10px] font-mono px-2 py-0.5 rounded-bl-lg text-white font-bold">
                  AGENT
                </div>
                <span className="text-xs text-slate-400 font-medium">ProofPilot (Grounded)</span>
                <div
                  className={`text-2xl font-bold font-mono mt-2 ${
                    metrics.proofpilot_net_return >= 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  ${metrics.proofpilot_net_return.toFixed(2)}
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  Challenges when Net EV &gt; $10 and evidence &gt; 40%. Accepts confirmed errors & loss-making claims.
                </p>
              </div>

              {/* Baseline 1: Contest Everything */}
              <div className="bg-slate-900/40 p-4 rounded-xl border border-slate-800">
                <span className="text-xs text-slate-400 font-medium">Baseline: Contest All</span>
                <div
                  className={`text-2xl font-bold font-mono mt-2 ${
                    metrics.contest_all_net_return >= 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  ${metrics.contest_all_net_return.toFixed(2)}
                </div>
                <p className="text-[11px] text-slate-500 mt-1">
                  Contests every chargeback indiscriminately. Suffers $40 fees on hopeless claims.
                </p>
              </div>

              {/* Baseline 2: Concede Everything */}
              <div className="bg-slate-900/40 p-4 rounded-xl border border-slate-800">
                <span className="text-xs text-slate-400 font-medium">Baseline: Concede All</span>
                <div className="text-2xl font-bold font-mono mt-2 text-slate-300">
                  ${metrics.concede_all_net_return.toFixed(2)}
                </div>
                <p className="text-[11px] text-slate-500 mt-1">
                  Accepts 100% of chargebacks without contesting. Zero fee risk, but leaves all recovery on the table.
                </p>
              </div>
            </div>
          </div>

          {/* Case-by-Case Breakdown Table */}
          <div className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-white tracking-tight">
              Test Case Simulation Details ({metrics.case_summaries.length} Cases Evaluated)
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-900 text-slate-400 uppercase font-mono text-[10px] border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Case ID</th>
                    <th className="py-2.5 px-3">Amount</th>
                    <th className="py-2.5 px-3">Recommendation</th>
                    <th className="py-2.5 px-3">Expected</th>
                    <th className="py-2.5 px-3">Simulated Outcome</th>
                    <th className="py-2.5 px-3">Grounding</th>
                    <th className="py-2.5 px-3 text-right">ProofPilot P&L</th>
                    <th className="py-2.5 px-3 text-right">Contest All P&L</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-sans">
                  {metrics.case_summaries.map((s) => (
                    <tr key={s.case_id} className="hover:bg-slate-900/30 transition-colors">
                      <td className="py-2.5 px-3 font-mono font-medium text-slate-200">{s.case_id}</td>
                      <td className="py-2.5 px-3 font-mono">${s.amount.toFixed(2)}</td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            s.recommendation === 'challenge'
                              ? 'bg-emerald-500/10 text-emerald-400'
                              : s.recommendation === 'accept'
                              ? 'bg-blue-500/10 text-blue-400'
                              : 'bg-amber-500/10 text-amber-400'
                          }`}
                        >
                          {s.recommendation}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-slate-400">{s.expected_recommendation}</td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`text-[11px] font-medium ${
                            s.simulated_win ? 'text-emerald-400' : 'text-slate-400'
                          }`}
                        >
                          {s.simulated_win ? 'Won' : 'Lost / Conceded'}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono">{(s.grounding_rate * 100).toFixed(0)}%</td>
                      <td className="py-2.5 px-3 font-mono text-right font-semibold">
                        <span className={s.proofpilot_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                          ${s.proofpilot_pnl.toFixed(2)}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-right text-slate-400">
                        ${s.contest_all_pnl.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
};
