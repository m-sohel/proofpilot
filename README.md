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

---

## 👥 Core Team & Project Roles

ProofPilot is developed through a disciplined, cross-functional engineering collaboration among three team members. The project unites core server-side architecture, payment dispute business logic, agentic workflow coordination, and a modern client-side user experience into an integrated, evidence-grounded dispute response application.

| Team Member | Primary Role | Technical Ownership & Responsibilities | Key Contributions |
|---|---|---|---|
| **[Kasim Shah](kasim-bio.md)** | **Backend Engineer & System Architecture** | Core backend implementation, server-side architecture, dispute lifecycle processing, REST API contracts, and business logic execution. | Spearheaded the primary server-side implementation; developed dispute lifecycle processing pipelines; designed predictable API endpoints; established clean service boundaries and architectural documentation. |
| **Sohel Shaikh** | **Project Lead & Backend Engineer** | Overall project leadership, technical roadmap coordination, backend agent workflows, SQLite audit logging, and evaluation pipelines. | Led project direction, milestone sequencing, and cross-component integration; contributed to backend dispute engines, adversarial issuer review, contradiction detection workflows, and benchmark tracking. |
| **Mariya Sayyed** | **Frontend Engineer** | Client-side application architecture, user experience design, responsive dashboard implementation, and API integration. | Built the responsive user interface using React 19, TypeScript, and Vite; styled accessible dispute-review interfaces with Tailwind CSS and Lucide icons; integrated frontend state with backend review endpoints. |

### Individual Engineering Ownership

#### Kasim Shah — Backend Engineering & System Architecture

Kasim owns the core backend implementation and primary server-side architecture of ProofPilot. His work establishes the engineering foundation that handles dispute data intake, business rules, API communication, and lifecycle state management.

- **Core Backend Architecture**: Structures the server-side application modules, defines service boundaries, and implements the primary operational workflows that underpin ProofPilot's backend.
- **Dispute Lifecycle & Business Logic**: Implements the server-side state machine and business rules governing how payment disputes are ingested, evaluated, and transitioned across lifecycle stages.
- **API & Service Integration**: Designs and implements RESTful API endpoints, request validation schemas, structured responses, and reliable error handling to support frontend interaction.
- **Evidence & Decision Processing**: Coordinates backend data pipelines for evidence organization, supporting contradiction checks and economics-based decision workflows with structured data models.
- **Reliability & Maintainability**: Maintains separation of concerns between API transport layers and core business logic, supporting backend unit testing, debugging, and system documentation.

*Role Boundary*: Kasim serves as the primary engineer responsible for building the core server-side codebase and backend workflows, distinct from project-level management and client-side interface development.

#### Sohel Shaikh — Project Leadership & Backend Engineering

Sohel serves as the Project Lead while actively contributing to backend systems engineering. His focus spans overall project direction, delivery alignment, and specialized backend agent workflows.

- **Project Leadership & Coordination**: Guides technical roadmap planning, task sequencing, and cross-functional coordination between backend and frontend development tracks.
- **Backend & Agent Workflow Development**: Contributes to backend services and dispute-processing workflows, coordinating how automated dispute intake connects with response generation stages.
- **Data Management & Auditability**: Supports database integration, data persistence, and append-only SQLite audit logging for dispute review actions and governance tracking.
- **Evaluation & Quality Assurance**: Implements and tracks contradiction-detection routines, adversarial issuer red-teaming checks, and benchmark evaluation suites to identify technical risks and measure response quality.
- **Integration & Delivery**: Oversees end-to-end integration between backend APIs and frontend components, verifying system milestones and demonstrable application flows.

*Role Boundary*: Sohel directs high-level project coordination, milestone execution, and agent evaluation systems, working in partnership with Kasim's core backend architecture.

#### Mariya Sayyed — Frontend Engineering

Mariya owns the frontend application architecture and user-facing experience of ProofPilot. She is responsible for translating complex backend dispute models into an intuitive, responsive interface for reviewers.

- **Frontend Architecture**: Organizes the client application directory structure, manages component hierarchies, and builds maintainable, modular client-side code.
- **User Interface & Experience**: Designs and develops the responsive dashboard layout, presenting dispute records, urgency indicators, financial risk metrics, and evidence summaries in a clear, digestible format.
- **Frontend Technologies**: Employs React 19, TypeScript, and Vite for modern component rendering and strict type safety, accompanied by Tailwind CSS for structured design and Lucide icons for visual clarity.
- **Client-Side State & Interaction**: Implements dispute-review workflows, selection queues, loading states, validation feedback, and action confirmations.
- **Backend API Integration**: Connects frontend views to backend endpoints, handling data fetching, response parsing, error banners, and human-in-the-loop dispute submission confirmations.

*Role Boundary*: Mariya focuses entirely on client-side interface implementation, interaction design, and frontend API integration, distinct from server-side infrastructure and backend business logic.

### Team Collaboration

ProofPilot's functionality depends on continuous, structured collaboration across engineering disciplines rather than isolated silos:

1. **Backend Infrastructure to API Delivery**: Core backend systems implemented by **Kasim Shah** establish reliable data models, validation schemas, and predictable API endpoints for dispute lifecycle operations.
2. **Project Direction & Intelligence Workflows**: Project leadership and backend contributions from **Sohel Shaikh** coordinate delivery milestones, integrate agent evaluation routines, and ensure transparent audit trails for governance.
3. **Interactive Review & Presentation**: The client interface engineered by **Mariya Sayyed** consumes backend APIs to deliver an intuitive, deadline-aware dispute triage experience that facilitates human-in-the-loop review.
4. **Lifecycle Alignment**: Ongoing communication across these areas ensures that API contracts, business logic assumptions, and user workflows remain synchronized throughout development.


