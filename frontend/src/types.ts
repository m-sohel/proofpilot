export type DisputeReason =
  | 'product_not_received'
  | 'duplicate_charge'
  | 'service_not_provided'
  | 'refund_not_processed';

export type CaseStatus = 'new' | 'analyzed' | 'drafted' | 'approved';

export type Recommendation = 'accept' | 'challenge' | 'escalate';

export type Severity = 'low' | 'medium' | 'high';

export type SentenceKind = 'claim' | 'boilerplate';

export type FixType = 'patch' | 'need_evidence' | 'escalate';

export type FactType =
  | 'order'
  | 'payment'
  | 'courier_event'
  | 'chat_message'
  | 'policy_clause'
  | 'refund'
  | 'usage_log'
  | 'completion_notice';

export interface Fact {
  id: string;
  type: FactType;
  ts: string | null;
  text: string;
  fields: Record<string, any>;
  source: string;
  confidence: number;
}

export interface Contradiction {
  id: string;
  rule_id: string;
  severity: Severity;
  fact_ids: string[];
  explanation: string;
}

export interface Economics {
  amount: number;
  expected_recovery: number;
  handling_cost: number;
  dispute_fee: number;
  net_ev: number;
}

export interface Decision {
  recommendation: Recommendation;
  reasons: string[];
  evidence_strength: number;
  p_win_estimate: number;
  economics: Economics;
  missing_evidence: string[];
  hours_left: number;
  requires_human_review: boolean;
  deadline_warning?: string | null;
}

export interface DraftSentence {
  text: string;
  evidence_ids: string[];
  kind: SentenceKind;
}

export interface GroundingReport {
  kept: DraftSentence[];
  removed: { text: string; reason: string }[];
  todos: string[];
}

export interface RedTeamFinding {
  weakness: string;
  why_it_loses: string;
  fix_type: FixType;
  related_fact_ids: string[];
}

export interface CaseArtifact {
  filename: string;
  content: string;
  artifact_type: string;
}

export interface DisputeCase {
  id: string;
  reason: DisputeReason;
  amount: number;
  currency: string;
  status: CaseStatus;
  created_at: string;
  deadline: string;
  merchant_name: string;
  customer_id: string;
  merchant_error: boolean;
  artifacts: CaseArtifact[];
  facts: Fact[];
  contradictions: Contradiction[];
  decision: Decision | null;
  draft: DraftSentence[];
  grounding_report: GroundingReport | null;
  redteam_findings: RedTeamFinding[];
  approved_at: string | null;
  approved_by: string | null;
}

export interface QueueItem {
  case_id: string;
  reason: DisputeReason;
  amount: number;
  hours_left: number;
  recommendation: Recommendation | null;
  score: number;
  score_breakdown: {
    net_ev: number;
    effort_hours: number;
    urgency: number;
    hours_left: number;
    is_overdue: number;
    amount: number;
  };
  is_overdue: boolean;
  deadline_warning: string | null;
}

export interface AuditEvent {
  id: string;
  case_id: string;
  action: string;
  actor: string;
  timestamp: string;
  payload: Record<string, any>;
}

export interface HealthResponse {
  status: string;
  llm_status: string;
  llm_provider: string;
  demo_mode: boolean;
}

export interface BenchmarkMetrics {
  total_cases: number;
  extraction_accuracy: number;
  contradiction_precision: number;
  contradiction_recall: number;
  grounding_rate: number;
  hallucinated_count: number;
  proofpilot_net_return: number;
  contest_all_net_return: number;
  concede_all_net_return: number;
  case_summaries: {
    case_id: string;
    amount: number;
    recommendation: string;
    expected_recommendation: string;
    simulated_win: boolean;
    extraction_accuracy: number;
    contradiction_precision: number;
    contradiction_recall: number;
    grounding_rate: number;
    hallucination_count: number;
    proofpilot_pnl: number;
    contest_all_pnl: number;
    concede_all_pnl: number;
  }[];
}
