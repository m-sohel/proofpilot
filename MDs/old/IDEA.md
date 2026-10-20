ProofPilot: An Evidence-Grounded, Economics-Aware Agent for Dispute Response

## TL;DR
ProofPilot treats every payment dispute as a **decision under uncertainty and a deadline**, not a writing task. It verifies the evidence, works out whether contesting is financially worth it, drafts a response where **every claim is traceable to proof**, and stress-tests that draft against the issuer's likely objections, all before a human approves it.

## The problem
Merchants lose money on disputes in three avoidable ways:
1. **Contesting the wrong cases.** Effort and fees exceed what can be recovered.
2. **Conceding winnable cases.** Proof is scattered across order systems, courier portals, support chats and policy pages.
3. **Submitting weak or inconsistent responses** that fail on a technicality, with a fixed deadline and a small team.

Generic LLM drafting makes this worse because it confidently invents facts, which is dangerous in a financial and legal workflow.

## Our solution: four engines and one queue
**1. Evidence Graph**
Ingests messy artifacts (order logs, courier events, chat transcripts, refund records, policy text) and builds a single case timeline. It automatically flags contradictions, such as a delivery scan earlier than dispatch, a shipping address that differs from the order, or a refund that isn't linked to this transaction. Evidence strength is scored per dispute reason.

**2. Dispute Economics Engine**
Computes the *net expected value of contesting*:
`(estimated win likelihood × recoverable amount) − (handling cost + dispute fee)`
It then recommends **Accept / Challenge / Escalate** with plain-language reasons. Win likelihood is shown as a labelled *estimate*, starting from transparent reason-code playbooks and becoming calibrated as case outcomes are logged.

**3. Claim-Grounded Drafting ("no evidence, no sentence")**
The LLM writes only from a structured fact sheet. Every sentence is tagged with an evidence ID, and a verifier blocks or flags any statement without support. Missing proof becomes a to-do item for the reviewer, never an invented detail.

**4. Issuer Red-Team**
A second, adversarial pass reads the draft the way a skeptical reviewer would. It lists the 3 likeliest reasons the response would lose and either patches the draft or escalates the case.

**+ Deadline-Aware Triage Queue**
Ranks all open disputes by net value, time remaining and effort, so a small team always works the right case first.

## Worked example (illustrative numbers)
- **₹18,400 "service not provided", 3 days left.** The graph finds usage logs and a completion email. The red-team notices the email was sent *before* the stated service end. The draft is rewritten to cite the usage log instead, and the one remaining gap (signed completion record) is listed as a to-do. **Result: Challenge.**
- **₹650 "duplicate charge".** Records confirm the duplicate, so contesting costs more than it could recover. **Result: Accept**, queued for human approval.
- **₹9,000 "product not received", contradictory courier events.** The evidence is too inconsistent to defend. **Result: Escalate** with the exact contradiction highlighted.

## What makes it different
| Typical approach | ProofPilot |
|---|---|
| Chatbot that writes a letter | Verifies evidence *before* writing |
| Static rules table | Economics-first decisions that account for cost, deadlines and effort |
| "Trust the AI" | Every claim is traceable to evidence |
| One-shot output | Adversarial self-review of the draft |
| Static logic | Learns from logged win/loss outcomes |

Reason-code playbooks are **configuration, not code** (JSON/YAML), so new card networks, UPI categories or wallet schemes can be added without redeploying the agent.

## Human control and responsible AI
- **Never auto-submits.** A human reviews and approves every response.
- Each recommendation shows its reasons, the evidence used and its confidence.
- Full audit trail of decisions, edits and approvals.
- Synthetic data only in the prototype, with PII masking by design.

## Build-round plan (feasible in the time available)
- **MVP:** case intake → evidence graph → economics decision → grounded draft → red-team critique → triage queue.
- **Stack:** fully open-source and zero-cost. Web UI, a lightweight backend with SQLite, and an open-weights LLM with schema-validated structured output. A deterministic template fallback keeps the demo working even if the model fails.
- **Evaluation:** a synthetic benchmark of ~50 disputes across 4 reason categories, comparing ProofPilot against two baselines ("contest everything" and "concede everything") on net recovery, response time, and % of draft claims fully grounded.

## Impact
Higher net recovery, faster responses, fewer technical rejections, and less analyst time spent on disputes that were never worth contesting.

## Roadmap
Payment-gateway webhooks, outcome-based learning, root-cause insights (e.g. disputes clustering around one courier, region or product), and multilingual response drafts.

**Team:** [Team name] · **Repo / prototype / demo link:** [add link]