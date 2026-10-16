import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  Play,
  FileCheck,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  Lock,
  Edit3,
  ExternalLink,
  ListTodo,
  Layers,
  Clock,
  UserCheck,
  X,
  FileText,
} from 'lucide-react';
import type {
  DisputeCase,
  DraftSentence,
  AuditEvent,
  SentenceKind,
} from '../types';
import { api } from '../api';

interface CaseViewProps {
  caseId: string;
  onBackToQueue: () => void;
  onRefreshQueue: () => void;
}

export const CaseView: React.FC<CaseViewProps> = ({
  caseId,
  onBackToQueue,
  onRefreshQueue,
}) => {
  const [caseData, setCaseData] = useState<DisputeCase | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Highlighting and interactive state
  const [highlightedFactId, setHighlightedFactId] = useState<string | null>(null);
  const [isEditingDraft, setIsEditingDraft] = useState(false);
  const [editedDraftText, setEditedDraftText] = useState('');
  const [activeTab, setActiveTab] = useState<'decision' | 'redteam' | 'todos' | 'audit'>('decision');

  // Approval modal state
  const [showApproveModal, setShowApproveModal] = useState(false);
  const [approverName, setApproverName] = useState('Senior Dispute Analyst');
  const [confirmApprove, setConfirmApprove] = useState(false);

  const loadCase = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getCase(caseId);
      setCaseData(data);
      const audit = await api.getAudit(caseId);
      setAuditEvents(audit);

      // Initialize edit text
      if (data.draft) {
        setEditedDraftText(
          data.draft.map((s) => `[${s.evidence_ids.join(', ')}] ${s.text}`).join('\n\n')
        );
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load case');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCase();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId]);

  const handleAnalyze = async () => {
    setActionLoading('analyze');
    setError(null);
    try {
      const updated = await api.analyzeCase(caseId);
      setCaseData(updated);
      const audit = await api.getAudit(caseId);
      setAuditEvents(audit);
      onRefreshQueue();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDraft = async () => {
    setActionLoading('draft');
    setError(null);
    try {
      const updated = await api.draftCase(caseId);
      setCaseData(updated);
      setEditedDraftText(
        updated.draft.map((s) => `[${s.evidence_ids.join(', ')}] ${s.text}`).join('\n\n')
      );
      const audit = await api.getAudit(caseId);
      setAuditEvents(audit);
      onRefreshQueue();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setActionLoading(null);
    }
  };

  const handleRedTeam = async () => {
    setActionLoading('redteam');
    setError(null);
    try {
      const updated = await api.redteamCase(caseId);
      setCaseData(updated);
      const audit = await api.getAudit(caseId);
      setAuditEvents(audit);
      setActiveTab('redteam');
      onRefreshQueue();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setActionLoading(null);
    }
  };

  const handleSaveDraft = async () => {
    setActionLoading('save_draft');
    setError(null);
    try {
      // Parse edited draft text back into DraftSentence array
      const rawBlocks = editedDraftText.split('\n\n').filter((b) => b.trim());
      const parsedSentences: DraftSentence[] = rawBlocks.map((block) => {
        const trimmed = block.trim();
        const match = trimmed.match(/^\[(.*?)\]\s*(.*)$/);
        if (match) {
          const ids = match[1]
            .split(',')
            .map((id) => id.trim())
            .filter((id) => id.length > 0);
          return {
            text: match[2],
            evidence_ids: ids,
            kind: ids.length > 0 ? ('claim' as SentenceKind) : ('boilerplate' as SentenceKind),
          };
        }
        return {
          text: trimmed,
          evidence_ids: [],
          kind: 'boilerplate' as SentenceKind,
        };
      });

      const updated = await api.updateDraft(caseId, parsedSentences);
      setCaseData(updated);
      setIsEditingDraft(false);
      const audit = await api.getAudit(caseId);
      setAuditEvents(audit);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setActionLoading(null);
    }
  };

  const handleApprove = async () => {
    if (!confirmApprove) return;
    setActionLoading('approve');
    setError(null);
    try {
      const updated = await api.approveCase(caseId, approverName, true);
      setCaseData(updated);
      setShowApproveModal(false);
      const audit = await api.getAudit(caseId);
      setAuditEvents(audit);
      onRefreshQueue();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="glass-panel rounded-2xl p-16 text-center border border-slate-800">
        <div className="inline-flex items-center gap-2 text-slate-400 text-sm">
          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          Loading case data and evidence graph...
        </div>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="glass-panel rounded-2xl p-12 text-center border border-slate-800">
        <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-white">Case Not Found</h3>
        <p className="text-xs text-slate-400 mt-1">Unable to locate dispute case with ID {caseId}.</p>
        <button
          onClick={onBackToQueue}
          className="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-medium"
        >
          Return to Queue
        </button>
      </div>
    );
  }

  const isApproved = caseData.status === 'approved';
  const hasFacts = caseData.facts.length > 0;
  const hasDecision = !!caseData.decision;
  const hasDraft = caseData.draft.length > 0;

  return (
    <div className="space-y-6">
      {/* Top Action & Breadcrumb Bar */}
      <div className="glass-panel rounded-2xl p-4 sm:p-5 border border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onBackToQueue}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 transition-colors"
            title="Return to triage queue"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-white font-mono">{caseData.id}</h1>
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/30">
                {caseData.reason.replace(/_/g, ' ').toUpperCase()}
              </span>
              {isApproved ? (
                <span className="flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  <Lock className="w-3 h-3" /> APPROVED
                </span>
              ) : (
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                  {caseData.status.toUpperCase()}
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Merchant: <strong className="text-slate-200">{caseData.merchant_name}</strong> • Disputed:{' '}
              <strong className="text-emerald-400">${caseData.amount.toFixed(2)}</strong>
            </p>
          </div>
        </div>

        {/* Pipeline Actions */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={handleAnalyze}
            disabled={actionLoading !== null || isApproved}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-200 transition-colors disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${actionLoading === 'analyze' ? 'animate-spin text-blue-400' : 'text-blue-400'}`} />
            <span>{hasFacts ? 'Re-Analyze' : '1. Analyze Evidence'}</span>
          </button>

          <button
            onClick={handleDraft}
            disabled={actionLoading !== null || isApproved}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-200 transition-colors disabled:opacity-50"
          >
            <FileCheck className={`w-3.5 h-3.5 ${actionLoading === 'draft' ? 'animate-spin text-indigo-400' : 'text-indigo-400'}`} />
            <span>{hasDraft ? 'Re-Draft' : '2. Grounded Draft'}</span>
          </button>

          <button
            onClick={handleRedTeam}
            disabled={actionLoading !== null || !hasDraft || isApproved}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-medium text-slate-200 transition-colors disabled:opacity-50"
          >
            <ShieldAlert className={`w-3.5 h-3.5 ${actionLoading === 'redteam' ? 'animate-spin text-rose-400' : 'text-rose-400'}`} />
            <span>3. Issuer Red-Team</span>
          </button>

          {!isApproved && (
            <button
              onClick={() => setShowApproveModal(true)}
              disabled={actionLoading !== null || !hasDraft}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-600/30 transition-colors disabled:opacity-50"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>4. Approve Response</span>
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 rounded-xl p-3 text-xs text-rose-300 flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)}><X className="w-4 h-4" /></button>
        </div>
      )}

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Evidence Graph & Timeline (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="glass-panel rounded-2xl p-4 sm:p-5 border border-slate-800">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-blue-400" />
                <h2 className="text-sm font-bold text-white tracking-tight">Evidence Graph & Timeline</h2>
              </div>
              <span className="text-xs font-mono text-slate-400">
                {caseData.facts.length} Verified Facts
              </span>
            </div>

            {/* Contradictions Banner */}
            {caseData.contradictions.length > 0 && (
              <div className="mb-4 space-y-2">
                {caseData.contradictions.map((c) => (
                  <div
                    key={c.id}
                    className={`p-3 rounded-xl border text-xs ${
                      c.severity === 'high'
                        ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                        : c.severity === 'medium'
                        ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                        : 'bg-slate-800 border-slate-700 text-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold flex items-center gap-1.5 uppercase tracking-wider text-[10px]">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Rule {c.rule_id} • {c.severity} Severity Contradiction
                      </span>
                      <span className="font-mono text-[10px] opacity-75">
                        Conflicting: {c.fact_ids.join(', ')}
                      </span>
                    </div>
                    <p className="text-[11px] leading-relaxed">{c.explanation}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Fact Timeline */}
            {!hasFacts ? (
              <div className="py-8 text-center text-slate-500 text-xs">
                No facts extracted yet. Click &quot;1. Analyze Evidence&quot; above to parse the raw artifacts into structured timeline events.
              </div>
            ) : (
              <div className="relative pl-6 space-y-4 before:content-[''] before:absolute before:left-2 before:top-2 before:bottom-2 before:w-[2px] before:bg-slate-800">
                {caseData.facts.map((fact) => {
                  const isHighlighted = highlightedFactId === fact.id;
                  const isContradicted = caseData.contradictions.some((c) => c.fact_ids.includes(fact.id));

                  return (
                    <div
                      key={fact.id}
                      id={`fact-${fact.id}`}
                      className={`relative p-3 rounded-xl border text-xs transition-all ${
                        isHighlighted
                          ? 'border-blue-500 bg-blue-500/10 shadow-md shadow-blue-500/20 ring-1 ring-blue-500'
                          : isContradicted
                          ? 'border-rose-500/40 bg-rose-500/5'
                          : 'border-slate-800 bg-slate-900/40 hover:border-slate-700'
                      }`}
                    >
                      {/* Node point */}
                      <span
                        className={`absolute -left-[27px] top-3.5 w-3 h-3 rounded-full border-2 ${
                          isHighlighted
                            ? 'bg-blue-400 border-blue-200 ring-2 ring-blue-500/50'
                            : isContradicted
                            ? 'bg-rose-500 border-slate-900'
                            : 'bg-slate-600 border-slate-900'
                        }`}
                      />

                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-blue-400 bg-blue-500/10 px-1.5 py-0.5 rounded text-[10px]">
                            {fact.id}
                          </span>
                          <span className="text-[10px] uppercase font-mono text-slate-400 bg-slate-800/80 px-1.5 py-0.5 rounded">
                            {fact.type}
                          </span>
                        </div>
                        {fact.ts && (
                          <span className="text-[10px] text-slate-500 font-mono flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {fact.ts.replace('T', ' ')}
                          </span>
                        )}
                      </div>

                      <p className="text-slate-200 text-xs leading-relaxed">{fact.text}</p>

                      {/* Fact Normalized Fields */}
                      {Object.keys(fact.fields).length > 0 && (
                        <div className="mt-2 pt-2 border-t border-slate-800/60 flex flex-wrap gap-1.5">
                          {Object.entries(fact.fields).map(([k, v]) => (
                            <span key={k} className="text-[10px] font-mono bg-slate-900 px-1.5 py-0.5 rounded text-slate-400 border border-slate-800">
                              <span className="text-slate-500">{k}:</span> {String(v)}
                            </span>
                          ))}
                        </div>
                      )}

                      <div className="mt-1 text-[10px] text-slate-500 font-mono">
                        Source: {fact.source}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Decision, Grounded Draft & Review (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Recommendation & Economics Card */}
          {hasDecision && (
            <div className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div
                    className={`px-3.5 py-1.5 rounded-xl font-bold text-sm tracking-wide shadow-md ${
                      caseData.decision!.recommendation === 'challenge'
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-emerald-500/10'
                        : caseData.decision!.recommendation === 'accept'
                        ? 'bg-blue-500/20 text-blue-300 border border-blue-500/40 shadow-blue-500/10'
                        : 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-amber-500/10'
                    }`}
                  >
                    RECOMMENDATION: {caseData.decision!.recommendation.toUpperCase()}
                  </div>
                  <span className="text-xs text-slate-400">
                    Est. Win Likelihood: <strong className="text-white font-mono">{(caseData.decision!.p_win_estimate * 100).toFixed(0)}%</strong>
                  </span>
                </div>

                <div className="text-xs font-mono text-slate-400">
                  Evidence Strength: <strong className="text-blue-400">{(caseData.decision!.evidence_strength * 100).toFixed(0)}%</strong>
                </div>
              </div>

              {/* Economics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
                <div className="bg-slate-900/60 p-2.5 rounded-xl border border-slate-800">
                  <span className="text-[10px] font-mono text-slate-500 block">Disputed Amount</span>
                  <span className="font-mono text-white font-semibold">${caseData.decision!.economics.amount.toFixed(2)}</span>
                </div>
                <div className="bg-slate-900/60 p-2.5 rounded-xl border border-slate-800">
                  <span className="text-[10px] font-mono text-slate-500 block">Expected Recovery</span>
                  <span className="font-mono text-emerald-400 font-semibold">${caseData.decision!.economics.expected_recovery.toFixed(2)}</span>
                </div>
                <div className="bg-slate-900/60 p-2.5 rounded-xl border border-slate-800">
                  <span className="text-[10px] font-mono text-slate-500 block">Handling + Fees</span>
                  <span className="font-mono text-slate-400">-${(caseData.decision!.economics.handling_cost + caseData.decision!.economics.dispute_fee).toFixed(2)}</span>
                </div>
                <div className="bg-slate-900/60 p-2.5 rounded-xl border border-slate-800">
                  <span className="text-[10px] font-mono text-slate-500 block">Net Expected Value</span>
                  <span
                    className={`font-mono font-bold text-sm ${
                      caseData.decision!.economics.net_ev > 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    ${caseData.decision!.economics.net_ev.toFixed(2)}
                  </span>
                </div>
              </div>

              {/* Decision Reasons */}
              <div className="space-y-1 text-xs text-slate-300">
                <span className="text-[10px] uppercase font-mono text-slate-500 block">Economic Rationale:</span>
                <ul className="list-disc pl-4 space-y-1">
                  {caseData.decision!.reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>

              {caseData.decision!.deadline_warning && (
                <div className="text-xs text-amber-400 bg-amber-500/10 border border-amber-500/20 px-3 py-1.5 rounded-lg flex items-center gap-2">
                  <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                  <span>{caseData.decision!.deadline_warning}</span>
                </div>
              )}
            </div>
          )}

          {/* Grounded Draft Workspace */}
          <div className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-indigo-400" />
                <h2 className="text-sm font-bold text-white tracking-tight">Evidence-Grounded Response Draft</h2>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  No Evidence, No Sentence
                </span>
              </div>

              {!isApproved && hasDraft && (
                <button
                  onClick={() => setIsEditingDraft(!isEditingDraft)}
                  className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 bg-slate-900 border border-slate-800 px-2.5 py-1 rounded-lg"
                >
                  <Edit3 className="w-3 h-3" />
                  <span>{isEditingDraft ? 'View Grounding' : 'Edit Draft'}</span>
                </button>
              )}
            </div>

            {!hasDraft ? (
              <div className="py-8 text-center text-slate-500 text-xs">
                Draft not generated yet. Click &quot;2. Grounded Draft&quot; to generate an evidence-verified response.
              </div>
            ) : isEditingDraft ? (
              <div className="space-y-3">
                <p className="text-[11px] text-slate-400">
                  Edit draft sentences. Keep citation tags like <code className="text-blue-400">[E1, E2]</code> before claims. The Grounding Verifier will strictly reject fabricated dates, amounts, or untraceable statements.
                </p>
                <textarea
                  value={editedDraftText}
                  onChange={(e) => setEditedDraftText(e.target.value)}
                  rows={8}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 font-sans focus:outline-none focus:border-blue-500 leading-relaxed"
                />
                <div className="flex justify-end gap-2">
                  <button
                    onClick={() => setIsEditingDraft(false)}
                    className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveDraft}
                    disabled={actionLoading === 'save_draft'}
                    className="px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md shadow-blue-600/30"
                  >
                    {actionLoading === 'save_draft' ? 'Re-Verifying...' : 'Save & Re-Verify'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {caseData.draft.map((sentence, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-slate-900/50 border border-slate-800 text-xs text-slate-200 leading-relaxed hover:border-slate-700 transition-colors"
                  >
                    <span>{sentence.text}</span>
                    <div className="mt-2 flex items-center gap-1.5 flex-wrap">
                      {sentence.kind === 'boilerplate' && (
                        <span className="text-[10px] font-mono text-slate-500 bg-slate-800/60 px-1.5 py-0.5 rounded">
                          Boilerplate (Whitelisted)
                        </span>
                      )}
                      {sentence.evidence_ids.map((eid) => (
                        <button
                          key={eid}
                          onClick={() => {
                            setHighlightedFactId(eid);
                            const el = document.getElementById(`fact-${eid}`);
                            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                          }}
                          className="flex items-center gap-1 text-[10px] font-mono bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 border border-blue-500/30 px-1.5 py-0.5 rounded transition-colors"
                          title="Click to highlight source fact in timeline"
                        >
                          <span>Evidence {eid}</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </button>
                      ))}
                    </div>
                  </div>
                ))}

                {/* Grounding Verifier Report Summary */}
                {caseData.grounding_report && (
                  <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                    <span className="flex items-center gap-1 text-emerald-400 font-medium">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Verifier: {caseData.grounding_report.kept.length} grounded sentences passed
                    </span>
                    {caseData.grounding_report.removed.length > 0 && (
                      <span className="text-rose-400 font-medium">
                        {caseData.grounding_report.removed.length} ungrounded claim(s) rejected
                      </span>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Secondary Tabs: Red-Team Findings, To-Dos, Audit Trail */}
          <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
            <div className="flex border-b border-slate-800 bg-slate-900/60 px-4">
              <button
                onClick={() => setActiveTab('decision')}
                className={`py-3 px-3 text-xs font-medium border-b-2 transition-colors ${
                  activeTab === 'decision'
                    ? 'border-blue-500 text-blue-400 font-semibold'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Issuer Red-Team ({caseData.redteam_findings.length})
              </button>

              <button
                onClick={() => setActiveTab('todos')}
                className={`py-3 px-3 text-xs font-medium border-b-2 transition-colors ${
                  activeTab === 'todos'
                    ? 'border-blue-500 text-blue-400 font-semibold'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Missing Proof & To-Dos (
                {(caseData.decision?.missing_evidence.length || 0) +
                  (caseData.grounding_report?.todos.length || 0)}
                )
              </button>

              <button
                onClick={() => setActiveTab('audit')}
                className={`py-3 px-3 text-xs font-medium border-b-2 transition-colors ${
                  activeTab === 'audit'
                    ? 'border-blue-500 text-blue-400 font-semibold'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                Audit Trail ({auditEvents.length})
              </button>
            </div>

            <div className="p-4 sm:p-5">
              {activeTab === 'decision' && (
                <div className="space-y-3">
                  {caseData.redteam_findings.length === 0 ? (
                    <div className="py-6 text-center text-slate-500 text-xs">
                      No red-team pass executed yet. Click &quot;3. Issuer Red-Team&quot; above to simulate an adversarial issuer review.
                    </div>
                  ) : (
                    caseData.redteam_findings.map((f, i) => (
                      <div
                        key={i}
                        className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs space-y-1.5"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-rose-300 flex items-center gap-1.5">
                            <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                            {f.weakness}
                          </span>
                          <span className="text-[10px] font-mono uppercase bg-slate-800 px-2 py-0.5 rounded text-slate-300">
                            Fix: {f.fix_type}
                          </span>
                        </div>
                        <p className="text-slate-400 text-[11px]">{f.why_it_loses}</p>
                      </div>
                    ))
                  )}
                </div>
              )}

              {activeTab === 'todos' && (
                <div className="space-y-2">
                  {caseData.decision?.missing_evidence.map((item, i) => (
                    <div key={`miss-${i}`} className="flex items-start gap-2 text-xs text-amber-300 bg-amber-500/5 p-2 rounded-lg border border-amber-500/20">
                      <ListTodo className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                      <span>Missing Required Evidence: <strong>{item}</strong></span>
                    </div>
                  ))}
                  {caseData.grounding_report?.todos.map((todo, i) => (
                    <div key={`todo-${i}`} className="flex items-start gap-2 text-xs text-slate-300 bg-slate-900 p-2 rounded-lg border border-slate-800">
                      <ListTodo className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                      <span>{todo}</span>
                    </div>
                  ))}
                  {(!caseData.decision?.missing_evidence.length && !caseData.grounding_report?.todos.length) && (
                    <div className="py-6 text-center text-slate-500 text-xs">
                      No pending evidentiary to-dos.
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'audit' && (
                <div className="space-y-2 font-mono text-[11px]">
                  {auditEvents.map((ev) => (
                    <div key={ev.id} className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-blue-400 uppercase font-semibold">{ev.action}</span>
                        <span className="text-slate-400">by {ev.actor}</span>
                      </div>
                      <span className="text-slate-500 text-[10px]">{ev.timestamp.replace('T', ' ').substring(0, 19)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Human Approval Confirmation Modal */}
      {showApproveModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel max-w-md w-full rounded-2xl p-6 border border-slate-800 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                <UserCheck className="w-5 h-5" />
                <span>Confirm Dispute Response Approval</span>
              </div>
              <button onClick={() => setShowApproveModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              In accordance with human-in-the-loop dispute governance, response submission requires explicit human confirmation. The system will never auto-submit.
            </p>

            <div className="space-y-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
              <label className="text-[11px] text-slate-400 block">
                Reviewer Full Name / ID:
                <input
                  type="text"
                  value={approverName}
                  onChange={(e) => setApproverName(e.target.value)}
                  className="mt-1 w-full bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </label>

              <label className="flex items-start gap-2 cursor-pointer pt-1">
                <input
                  type="checkbox"
                  checked={confirmApprove}
                  onChange={(e) => setConfirmApprove(e.target.checked)}
                  className="mt-0.5 rounded border-slate-700 text-emerald-600 focus:ring-emerald-500"
                />
                <span className="text-xs text-slate-200">
                  I confirm that I have reviewed the evidence timeline, verified draft citations, and approve contesting or settling this dispute.
                </span>
              </label>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowApproveModal(false)}
                className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300"
              >
                Cancel
              </button>
              <button
                onClick={handleApprove}
                disabled={!confirmApprove || actionLoading === 'approve'}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-md shadow-emerald-600/30 disabled:opacity-50"
              >
                {actionLoading === 'approve' ? 'Approving...' : 'Sign & Approve Response'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
