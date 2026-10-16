# ProofPilot — AI Agent for Evidence-Grounded Payment Dispute Response

ProofPilot is an AI agent that empowers merchants to handle payment chargebacks with evidence-grounded, economically rational decisions. 

**Core Guarantee**: "No evidence, no sentence". Every claim cited in a response draft is verified by pure code against ground-truth facts. The LLM is strictly confined to extraction and drafting—**the LLM never decides whether to accept or challenge a dispute.**

---

## ⚡ Quick Start

### 1. Environment Setup
```bash
cp .env.example .env
```
Default configuration uses `LLM_PROVIDER=mock`, which provides 100% deterministic, offline demo fixtures with **zero external dependencies and zero cost**.

### 2. Run Tests
```bash
# Run the 30-test suite (contradictions, economics, triage, adversarial verifier, integration)
backend/venv/Scripts/pytest.exe -v
```

### 3. Run Benchmark
```bash
# Run benchmark on the 20% holdout test split
backend/venv/Scripts/python.exe eval/run_benchmark.py

# Or evaluate across all 50 synthetic dispute cases
backend/venv/Scripts/python.exe eval/run_benchmark.py --all
```

### 4. Start the Application
In terminal 1 (Backend):
```bash
backend/venv/Scripts/uvicorn.exe app.main:app --app-dir backend --reload --port 8000
```

In terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🧠 Key Innovations & Architecture

1. **Evidence Graph & Deterministic Contradictions**:
   Extracts structured facts from messy artifacts (courier logs, chats, orders, policies) and applies deterministic rules (**C1–C6**) to flag physical impossibilities (delivery before dispatch, address mismatch, duplicate charges without second settlement).

2. **Economics Engine**:
   Computes Net Expected Value:
   $$\text{Net EV} = (\hat{p}_{\text{win}} \times \text{Disputed Amount}) - (\text{Handling Cost} + \text{Dispute Fee})$$
   Automatically recommends **Accept** if fighting costs more than recovery ($\text{Net EV} \le 0$) or confirmed merchant error, **Escalate** if high contradictions exist or evidence is borderline, and **Challenge** only when mathematically justified.

3. **Grounding Verifier ("No Evidence, No Sentence")**:
   Pure-code verifier (no LLM) that checks every draft sentence. Rejects any fabricated dates, hallucinated tracking numbers, fake dollar amounts, nonexistent evidence IDs, or absolute promises ("guaranteed", "will definitely").

4. **Adversarial Issuer Red-Team**:
   Simulates bank issuer arbitration scrutiny to surface top 3 weaknesses, automatically routing them to auto-patch, missing proof checklist, or escalation.

5. **Deadline-Aware Triage Queue**:
   Ranks open disputes by capital at risk, effort hours, and countdown urgency multiplier ($1.0\times$, $1.5\times$, $2.0\times$, with overdue cases pinned to top).

6. **Human-in-the-Loop Governance**:
   Strict rule: **The system never auto-submits responses.** Submission requires explicit human confirmation and signs with the reviewer's ID into an append-only SQLite audit log.

---

## 📊 Evaluation & Financial Performance

Benchmarked across 50 seeded synthetic dispute cases (`eval/run_benchmark.py`):

| Evaluation Metric | Benchmark Result | Target / Baseline |
| :--- | :--- | :--- |
| **Extraction Accuracy** | **77.0%** | $> 75\%$ |
| **Contradiction Recall** | **90.0%** | $> 80\%$ |
| **Grounding Verification Rate** | **100.0%** | 100% |
| **Hallucinated Entities** | **0** | **0** |
| **ProofPilot Net Return** | **$0.00** | Non-negative |
| **Baseline: Contest Everything** | **-$400.00** | Indiscriminate fees |
| **Net Value Added** | **+$400.00** | Preserved capital |

*Disclaimer: All benchmark metrics and financial returns derive from synthetic dispute data and a simulated outcome model. See [docs/EVALUATION.md](docs/EVALUATION.md) for full methodology.*

---

## 🛠️ Tech Stack & Constraints

- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLite (stdlib `sqlite3`), Pytest, Ruff.
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, Lucide Icons.
- **Cost**: **Rs 0**. Completely free, open-source tools only. No billing or paid APIs required.
