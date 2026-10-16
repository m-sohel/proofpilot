# ProofPilot Architecture Documentation

ProofPilot is an AI agent for payment-dispute response built under hard constraints: zero API cost, synthetic data only, pure deterministic decisions (the LLM never decides whether to accept or challenge), and strict sentence-level evidence grounding ("no evidence, no sentence").

---

## 1. System Architecture Overview

```
                      ┌─────────────────────────────────────────┐
                      │            Raw Messy Evidence           │
                      │ (Courier Logs, Chats, Orders, Policies) │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │             Fact Extractor              │
                      │  (LLM json_guard / Deterministic Fallback)
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │      Evidence Graph & Contradictions    │
                      │     Deterministic Rules (C1 – C6)       │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │           Economics Engine              │
                      │      p_win_estimate, net_ev, Dec.       │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │           Grounded Drafter              │
                      │   Receives ONLY Facts & Economics Rec   │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │          Grounding Verifier             │
                      │   Pure Code Regex & Entity Validation   │
                      │    (Rejects fake dates, amounts, IDs)   │
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │          Issuer Red-Team Pass           │
                      │   Top 3 Weaknesses -> Patch/Todo/Escalate
                      └────────────────────┬────────────────────┘
                                           │
                                           ▼
                      ┌─────────────────────────────────────────┐
                      │          Human Approval Loop            │
                      │  Explicit Confirmation — Never Auto-Sub │
                      └─────────────────────────────────────────┘
```

---

## 2. Core Modules & Principles

### A. Fact Extraction (`app/extraction/`)
- Turns heterogeneous, unstructured evidence (courier logs, chat transcripts, order records, refund slips, terms of service) into structured `Fact` objects.
- Preserves verbatim strings for dates, dollar amounts, tracking numbers, and identifiers.
- Robust JSON guard with retries and deterministic fixture fallback so the demo never fails even when an LLM is offline or uninstalled.

### B. Deterministic Contradiction Rules (`app/evidence/contradictions.py`)
Deterministic rules that catch falsified, conflicting, or corrupted evidence:
- **C1: Delivery Before Dispatch (High Severity)** — Delivery event timestamp precedes courier dispatch.
- **C2: Address Mismatch (High Severity)** — Order shipping address does not match courier delivery address.
- **C3: Unlinked Refund (Medium Severity)** — Refund record not matched to any payment transaction.
- **C4: Premature Completion Notice (Medium Severity)** — Service completion timestamp is earlier than the service start/end period.
- **C5: Duplicate Claim without Settlement (High Severity)** — Multiple charges share identical transaction ID without second settlement.
- **C6: Evidence After Deadline (Low Severity)** — Evidence recorded after the dispute deadline.

### C. Economics Decision Engine (`app/decision/economics.py`)
The LLM **never** decides whether to contest. Recommendation is computed via deterministic code:
1. **Evidence Strength**:
   $$\text{evidence\_strength} = \frac{\sum \text{weight of present, uncontradicted evidence}}{\text{total required weight}}$$
2. **Win Probability Estimate**:
   $$\hat{p}_{\text{win}} = \text{clamp}(\text{evidence\_strength} - \text{penalties}, 0.02, 0.95)$$
3. **Net Expected Value**:
   $$\text{Net EV} = (\hat{p}_{\text{win}} \times \text{Disputed Amount}) - (\text{Handling Cost} + \text{Dispute Fee})$$
4. **Decision Priority Order**:
   - Confirmed Merchant Error $\rightarrow$ **ACCEPT**
   - High-severity contradiction detected $\rightarrow$ **ESCALATE**
   - $\text{Net EV} > \text{threshold}$ AND $\text{evidence\_strength} > \text{minimum}$ $\rightarrow$ **CHALLENGE**
   - $\text{Net EV} \le 0$ $\rightarrow$ **ACCEPT** (economic rationale: fighting costs more than recovery)
   - Otherwise $\rightarrow$ **ESCALATE** (borderline evidence requires human review)

### D. Grounded Drafting & Verifier (`app/drafting/`)
- **Drafter**: Input is strictly constrained to the extracted `Fact[]` and the `Decision`. Forbidden from using outside knowledge. Output is a JSON array of `DraftSentence`.
- **Grounding Verifier (Pure Code, No LLM)**:
  - Every claim sentence **must** cite at least one valid evidence ID.
  - Every cited ID must exist in the fact set.
  - Every date (`YYYY-MM-DD`), amount (`$XX.XX`), order ID (`ORD-XX`), transaction ID (`TXN-XX`), tracking number (`TRK-XX`), and customer name must appear in the cited facts.
  - Absolute promises ("guaranteed", "will definitely", "100% sure") are strictly rejected.
  - Uncited or hallucinated sentences are stripped and converted into to-dos.

### E. Adversarial Issuer Red-Team (`app/drafting/redteam.py`)
- Evaluates the response draft from the perspective of an adversarial card issuer / bank.
- Identifies the top 3 weaknesses:
  - **Patch**: Tightens ambiguous phrasing via a single controlled re-draft iteration.
  - **Need Evidence**: Adds specific proof requirements to the merchant's to-do list.
  - **Escalate**: Overrides the decision to Escalate if a fatal issue is uncovered.

### F. Deadline-Aware Triage Queue (`app/decision/triage.py`)
Ranks open disputes to prioritize high-value, time-critical chargebacks:
$$\text{Score} = \left(\frac{\max(\text{Net EV}, 0)}{\text{Effort Hours}}\right) \times \text{Urgency Multiplier}$$
- Urgency: $1.0\times$ ($>72\text{h}$ left), $1.5\times$ ($24-72\text{h}$ left), $2.0\times$ ($<24\text{h}$ left).
- Overdue disputes are pinned to the top of the queue with alert warnings.
- Escalate disputes rank by $\text{Amount} \times \text{Urgency}$.

### G. Human-in-the-Loop Governance (`app/storage/`)
- The system **never auto-submits responses**.
- Approval requires explicit confirmation (`confirm=True`) and reviewer identification.
- An append-only SQLite audit log (`audit_events`) tracks every lifecycle event: `created`, `analyzed`, `drafted`, `redteamed`, `edited`, and `approved`.
