import React, { useState } from 'react';
import {
  Clock,
  ArrowRight,
  TrendingUp,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Search,
  Filter,
  DollarSign,
  Layers,
  Sparkles,
} from 'lucide-react';
import type { QueueItem, DisputeReason } from '../types';

interface QueueViewProps {
  queue: QueueItem[];
  loading: boolean;
  onSelectCase: (caseId: string) => void;
  onSeed: () => void;
}

export const QueueView: React.FC<QueueViewProps> = ({
  queue,
  loading,
  onSelectCase,
  onSeed,
}) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [reasonFilter, setReasonFilter] = useState<string>('all');
  const [urgencyFilter, setUrgencyFilter] = useState<string>('all');

  const filteredItems = queue.filter((item) => {
    const matchesSearch = item.case_id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesReason = reasonFilter === 'all' || item.reason === reasonFilter;
    const matchesUrgency =
      urgencyFilter === 'all' ||
      (urgencyFilter === 'overdue' && item.is_overdue) ||
      (urgencyFilter === 'high' && !item.is_overdue && item.hours_left < 24) ||
      (urgencyFilter === 'medium' && !item.is_overdue && item.hours_left >= 24 && item.hours_left < 72) ||
      (urgencyFilter === 'low' && !item.is_overdue && item.hours_left >= 72);

    return matchesSearch && matchesReason && matchesUrgency;
  });

  const totalExposure = queue.reduce((sum, item) => sum + item.amount, 0);
  const overdueCount = queue.filter((item) => item.is_overdue).length;
  const urgentCount = queue.filter((item) => !item.is_overdue && item.hours_left < 24).length;

  const getReasonLabel = (reason: DisputeReason) => {
    switch (reason) {
      case 'product_not_received':
        return 'Product Not Received';
      case 'duplicate_charge':
        return 'Duplicate Charge';
      case 'service_not_provided':
        return 'Service Not Provided';
      case 'refund_not_processed':
        return 'Refund Not Processed';
      default:
        return reason;
    }
  };

  const getRecBadge = (rec: string | null) => {
    if (!rec) {
      return (
        <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700">
          Unanalyzed
        </span>
      );
    }
    switch (rec) {
      case 'challenge':
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            CHALLENGE
          </span>
        );
      case 'accept':
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/30">
            ACCEPT
          </span>
        );
      case 'escalate':
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
            ESCALATE
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* KPI Stats Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel rounded-2xl p-4 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Triage Queue Size</span>
            <Layers className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-white tracking-tight">{queue.length}</div>
          <div className="mt-1 text-xs text-slate-500">Active merchant disputes</div>
        </div>

        <div className="glass-panel rounded-2xl p-4 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Total Capital at Risk</span>
            <DollarSign className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-white tracking-tight">
            ${totalExposure.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="mt-1 text-xs text-slate-500">Gross disputed amount</div>
        </div>

        <div className="glass-panel rounded-2xl p-4 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Overdue Cases</span>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-rose-400 tracking-tight">{overdueCount}</div>
          <div className="mt-1 text-xs text-rose-400/80">Pinned to top of queue</div>
        </div>

        <div className="glass-panel rounded-2xl p-4 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Critical (&lt;24h)</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-amber-400 tracking-tight">{urgentCount}</div>
          <div className="mt-1 text-xs text-slate-500">Urgency multiplier: 2.0x</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-panel rounded-2xl p-4 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1 min-w-[280px]">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by Case ID (e.g., CASE-0001)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={reasonFilter}
              onChange={(e) => setReasonFilter(e.target.value)}
              className="bg-transparent text-slate-300 focus:outline-none text-xs cursor-pointer"
            >
              <option value="all">All Dispute Reasons</option>
              <option value="product_not_received">Product Not Received</option>
              <option value="duplicate_charge">Duplicate Charge</option>
              <option value="service_not_provided">Service Not Provided</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={urgencyFilter}
              onChange={(e) => setUrgencyFilter(e.target.value)}
              className="bg-transparent text-slate-300 focus:outline-none text-xs cursor-pointer"
            >
              <option value="all">All Urgency Levels</option>
              <option value="overdue">Overdue Only</option>
              <option value="high">Critical (&lt; 24h)</option>
              <option value="medium">Medium (24-72h)</option>
              <option value="low">Standard (&gt; 72h)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Queue Table */}
      {loading ? (
        <div className="glass-panel rounded-2xl p-12 text-center border border-slate-800">
          <div className="inline-flex items-center gap-2 text-slate-400 text-sm">
            <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            Loading deadline-ranked queue...
          </div>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="glass-panel rounded-2xl p-12 text-center border border-slate-800">
          <Sparkles className="w-8 h-8 text-slate-500 mx-auto mb-3" />
          <h3 className="text-sm font-semibold text-white">No disputes found in queue</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
            {queue.length === 0
              ? 'Database is currently empty. Click "Seed Data" to generate 50 realistic synthetic cases.'
              : 'No open cases match your current search and filter criteria.'}
          </p>
          {queue.length === 0 && (
            <button
              onClick={onSeed}
              className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-xl text-xs font-semibold text-white transition-colors"
            >
              Seed 50 Cases Now
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {filteredItems.map((item, index) => {
            const isExpanded = expandedId === item.case_id;

            return (
              <div
                key={item.case_id}
                className={`glass-panel rounded-2xl border transition-all ${
                  item.is_overdue
                    ? 'border-rose-500/30 bg-rose-500/[0.02]'
                    : item.hours_left < 24
                    ? 'border-amber-500/30 bg-amber-500/[0.02]'
                    : 'border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="p-4 sm:p-5 flex flex-wrap items-center justify-between gap-4">
                  {/* Left: Rank & Identification */}
                  <div className="flex items-center gap-3">
                    <span
                      className={`w-7 h-7 rounded-lg flex items-center justify-center font-mono text-xs font-bold ${
                        item.is_overdue
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : index === 0
                          ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      #{index + 1}
                    </span>

                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-sm text-white">{item.case_id}</span>
                        <span className="text-[11px] font-medium text-slate-400 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded-full">
                          {getReasonLabel(item.reason)}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 mt-1">
                        Disputed Amount:{' '}
                        <strong className="text-slate-200">
                          ${item.amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        </strong>
                      </div>
                    </div>
                  </div>

                  {/* Center: Deadline & Recommendation */}
                  <div className="flex items-center gap-4 flex-wrap">
                    {/* Urgency Pill */}
                    <div className="flex items-center gap-1.5">
                      <Clock
                        className={`w-3.5 h-3.5 ${
                          item.is_overdue
                            ? 'text-rose-400 animate-pulse'
                            : item.hours_left < 24
                            ? 'text-amber-400'
                            : 'text-slate-400'
                        }`}
                      />
                      <span
                        className={`text-xs font-semibold ${
                          item.is_overdue
                            ? 'text-rose-400'
                            : item.hours_left < 24
                            ? 'text-amber-400'
                            : 'text-slate-300'
                        }`}
                      >
                        {item.is_overdue ? 'OVERDUE' : `${item.hours_left.toFixed(1)}h remaining`}
                      </span>
                    </div>

                    {/* Recommendation Pill */}
                    <div>{getRecBadge(item.recommendation)}</div>

                    {/* Score Tag with Why Expander */}
                    <button
                      onClick={() => setExpandedId(isExpanded ? null : item.case_id)}
                      className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-xs text-slate-300 transition-colors"
                      title="Explain triage ranking score"
                    >
                      <span className="text-slate-400">Score:</span>
                      <span className="font-mono font-semibold text-blue-400">
                        {item.score > 900000 ? 'PINNED' : item.score.toFixed(1)}
                      </span>
                      {isExpanded ? <ChevronUp className="w-3 h-3 text-slate-400" /> : <ChevronDown className="w-3 h-3 text-slate-400" />}
                    </button>
                  </div>

                  {/* Right: Open Case CTA */}
                  <div>
                    <button
                      onClick={() => onSelectCase(item.case_id)}
                      className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md shadow-blue-600/20 transition-all hover:translate-x-0.5"
                    >
                      <span>Open Workspace</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* 'Why this rank' Expander Panel */}
                {isExpanded && (
                  <div className="border-t border-slate-800/80 bg-slate-950/60 p-4 sm:p-5 rounded-b-2xl">
                    <div className="flex items-center gap-2 text-xs font-semibold text-slate-300 mb-2">
                      <TrendingUp className="w-4 h-4 text-blue-400" />
                      <span>Triage Scoring Breakdown & Formula</span>
                    </div>

                    <div className="text-xs text-slate-400 mb-3 font-mono bg-slate-900 border border-slate-800 p-2.5 rounded-lg">
                      {item.is_overdue ? (
                        <span className="text-rose-300">
                          OVERDUE RULE: Score = 1,000,000 + (Amount ${item.amount.toFixed(2)} × Urgency {item.score_breakdown.urgency}x) = {item.score.toFixed(1)}
                        </span>
                      ) : item.recommendation === 'escalate' ? (
                        <span className="text-amber-300">
                          ESCALATE RULE: Score = Amount ${item.amount.toFixed(2)} × Urgency {item.score_breakdown.urgency}x = {item.score.toFixed(1)}
                        </span>
                      ) : (
                        <span className="text-emerald-300">
                          NORMAL RULE: Score = (max(Net EV ${item.score_breakdown.net_ev.toFixed(2)}, 0) / {item.score_breakdown.effort_hours}h effort) × Urgency {item.score_breakdown.urgency}x = {item.score.toFixed(1)}
                        </span>
                      )}
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                      <div className="bg-slate-900/40 p-2 rounded-lg border border-slate-800">
                        <span className="text-slate-500 text-[10px] uppercase font-mono block">Net EV</span>
                        <span className="font-mono text-white font-semibold">
                          ${item.score_breakdown.net_ev.toFixed(2)}
                        </span>
                      </div>
                      <div className="bg-slate-900/40 p-2 rounded-lg border border-slate-800">
                        <span className="text-slate-500 text-[10px] uppercase font-mono block">Effort Required</span>
                        <span className="font-mono text-white font-semibold">
                          {item.score_breakdown.effort_hours} hour
                        </span>
                      </div>
                      <div className="bg-slate-900/40 p-2 rounded-lg border border-slate-800">
                        <span className="text-slate-500 text-[10px] uppercase font-mono block">Urgency Multiplier</span>
                        <span className="font-mono text-white font-semibold">
                          {item.score_breakdown.urgency}x ({item.hours_left.toFixed(1)}h left)
                        </span>
                      </div>
                      <div className="bg-slate-900/40 p-2 rounded-lg border border-slate-800">
                        <span className="text-slate-500 text-[10px] uppercase font-mono block">Final Triage Score</span>
                        <span className="font-mono text-blue-400 font-bold">
                          {item.score.toFixed(1)}
                        </span>
                      </div>
                    </div>

                    {item.deadline_warning && (
                      <div className="mt-3 text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 px-3 py-1.5 rounded-lg flex items-center gap-2">
                        <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                        <span>{item.deadline_warning}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
