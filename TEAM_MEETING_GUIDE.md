# 🛡️ ProofPilot: The Future of AI-Powered Payment Dispute Response

> 💡 **Welcome Team!**  
> This document is our project briefing and discussion deck for our **Hackathon Idea Submission** (Deadline: **October 23, 2026**).  
> Today, we're discussing the problem we're solving, our proposed solution, a live demo of the prototype we've built, and our roadmap for the building phase.

---

## 📍 Part 1: The Real-World Problem (With Real Scenarios)

### 📦 Story 1: The "Package on Porch" Mystery (Product Not Received)
1. **The Order:** A customer buys a **\$200 pair of sneakers** from an online sneaker brand.
2. **The Delivery:** FedEx delivers the box to the front porch on Tuesday at 2:00 PM.
3. **The Dispute (Friendly Fraud):** On Friday, the customer contacts their bank (Chase/Citi) and clicks *"Dispute Charge: I never received my order."*
4. **The Merchant's Shock:** 
   - The bank immediately takes back the **\$200** from the sneaker brand's account.
   - The bank also charges the merchant a **non-refundable \$25 dispute fee**.
   - The bank gives the merchant **only 7 days** to prove the customer got the shoes.
5. **The Nightmare:** The merchant's staff has to log into Shopify to get the receipt, log into FedEx to download the tracking history, log into Zendesk to see if the customer chatted with support, and write a formal legal letter. If they miss the deadline or miss a detail, **they lose \$225 permanently**.

---

### 💳 Story 2: The "Double Charge" Confusion (Duplicate Charge)
1. A customer buys a monthly software subscription or clothing order for **\$80**.
2. Due to a small payment gateway retry glitch, two transactions occur: `TXN-001` and `TXN-001`.
3. The customer disputes both charges.
4. If the merchant doesn't catch this quickly and blindly fights both disputes, the bank rules against the merchant, penalizing them with **\$50 in penalty fees** on an \$80 order!

---

### 🛑 Why Merchants Are Losing This Battle Today

| The Problem Today | Why It Hurts Online Businesses |
| :--- | :--- |
| **1. Evidence is Scattered** | Proof is buried across 4 different platforms (Shopify receipts, FedEx tracking PDFs, customer chat logs, store return policy text). |
| **2. Contesting Costs More Than The Item** | Preparing a manual response takes 45 minutes of staff time ($\approx \$15$ labor) + \$25 bank fee = **\$40 overhead**. If a dispute is for a \$30 t-shirt, **fighting it guarantees a net loss even if you win!** |
| **3. Strict Countdown Deadlines** | Card issuers (Visa/Mastercard) enforce strict 7-to-14 day deadlines. Miss it by 1 hour, and the merchant forfeits the money automatically. |
| **4. Why "Just Using ChatGPT" Fails Disastrously** | If an employee pastes the order into ChatGPT and asks for a response letter, **the AI hallucinates**: it invents believable dates, fake tracking numbers, or makes claims like *"we guarantee delivery"*. Card issuer arbitration rules state that **a single unproven claim causes an instant loss**. |

> 📊 **Market Impact:** Online merchants lose over **\$100 Billion** annually to chargebacks and friendly fraud. It is one of the biggest hidden drains on e-commerce profit margins.

---

## 💡 Part 2: What We Are Proposing (Our Solution: ProofPilot)

**ProofPilot** is an intelligent AI copilot designed specifically for merchant fraud and dispute operations teams. 

Instead of an employee spending hours digging through logs and writing letters, ProofPilot automates the entire investigation and response workflow in **seconds**—with **zero hallucinations**.

```
                ┌────────────────────────────────────────────────────────┐
                │             MESSY UNSTRUCTURED EVIDENCE                │
                │   (Courier scans, customer chats, receipts, policies)   │
                └───────────────────────────┬────────────────────────────┘
                                            │
                                            ▼
                ┌────────────────────────────────────────────────────────┐
                │                1. AI Fact Extractor                    │
                │        Transforms messy files into clean facts         │
                └───────────────────────────┬────────────────────────────┘
                                            │
                                            ▼
                ┌────────────────────────────────────────────────────────┐
                │          2. Deterministic Contradiction Checks         │
                │        Catches data errors (C1 - C6 code rules)        │
                └───────────────────────────┬────────────────────────────┘
                                            │
                                            ▼
                ┌────────────────────────────────────────────────────────┐
                │                 3. Economics Engine                    │
                │   Calculates Net Expected Value: Is it worth fighting? │
                │        [ACCEPT / CHALLENGE / ESCALATE]                 │
                └───────────────────────────┬────────────────────────────┘
                                            │
                                            ▼
                ┌────────────────────────────────────────────────────────┐
                │     4. Grounded Drafter & Pure-Code Verifier           │
                │        "NO EVIDENCE, NO SENTENCE" (0 Hallucinations)   │
                └───────────────────────────┬────────────────────────────┘
                                            │
                                            ▼
                ┌────────────────────────────────────────────────────────┐
                │               5. Issuer Red-Team Pass                  │
                │       Adversarial AI stress-tests defense before bank  │
                └───────────────────────────┬────────────────────────────┘
                                            │
                                            ▼
                ┌────────────────────────────────────────────────────────┐
                │             6. Human Review & Approval                 │
                │           Explicit human signoff — Never auto-submit   │
                └────────────────────────────────────────────────────────┘
```

---

## 🔑 Part 3: The 4 Core Innovations of ProofPilot

### Innovation #1: The AI Never Chooses the Decision
> **Core Principle:** *The AI does the reading and the writing; pure math code does the decisions.*
- We never ask an LLM: *"Should we fight this dispute?"* (LLMs are not reliable at legal/financial decisions).
- Instead, our **Economics Engine** calculates the math:
  $$\text{Net Expected Value (Net EV)} = (\text{Win Likelihood} \times \text{Disputed Amount}) - (\text{Handling Cost } \$15 + \text{Dispute Fee } \$25)$$
- **Clear Rules:**
  - If $\text{Net EV} \le 0 \rightarrow$ **ACCEPT** (Conceding the \$20 item saves \$40 in fees!).
  - If confirmed merchant error $\rightarrow$ **ACCEPT** immediately.
  - If fatal contradiction found $\rightarrow$ **ESCALATE** to a manager.
  - If $\text{Net EV} > \$10$ and evidence is strong $\rightarrow$ **CHALLENGE** (Fight to win).

---

### Innovation #2: "No Evidence, No Sentence" (0 Hallucinations)
- In ProofPilot, every claim sentence written by the AI must cite verified facts:  
  `"Order ORD-992 was delivered on 2025-04-02 to 123 Oak St [E1, E3]."`
- A separate **pure-code verifier (zero AI)** inspects every single word:
  - Does `ORD-992` exist in the uploaded order slip? ✅
  - Does the date `2025-04-02` match the courier timestamp? ✅
  - Does the sentence say *"guaranteed"* or *"100% sure"*? ❌ **Rejected** (Absolute promises are removed).
- **Result:** $100\%$ factual grounding. Zero fake tracking numbers or dates.

---

### Innovation #3: The Adversarial Issuer Red-Team
- Before a human clicks send, a secondary AI plays the role of the **adversarial bank auditor**.
- It asks: *"If I were the customer's bank, how would I reject this merchant's defense?"*
- It flags the top 3 weaknesses (e.g., *"Tracking shows delivered, but no signature proof was attached"*) so the merchant can fix them before submitting.

---

### Innovation #4: Human-in-the-Loop Governance
- Chargeback responses are legal financial submissions to Visa and Mastercard.
- **ProofPilot NEVER auto-submits.**
- A human operator must review the timeline, inspect the draft, check the confirmation box, and sign off. Every action is recorded in an immutable **Audit Trail**.

---

## 🖥️ Part 4: Live Demo Walkthrough (What We Have Built Right Now)

> 🌟 **Our Unfair Advantage:** While other teams submitting on Oct 23 only have slides or Figma wireframes, **we already have a fully functioning, tested MVP running right now!**

### Step 1: The Triage Queue Screen
- Open `http://localhost:5173` $\rightarrow$ Click **"Triage Queue"**.
- Point out:
  - Disputes are ranked by deadline countdown and capital exposure.
  - Cases with **< 24 hours left** get an automatic **2.0x urgency multiplier**.
  - Overdue cases are **pinned to the top** in flashing red alert.
  - Click the **"Score"** button to show the team the exact mathematical scoring formula breakdown.

### Step 2: The Evidence Graph & Contradiction Detection
- Open **`CASE-0029`** (or click any case).
- Point to the left column:
  - **30 Verified Facts** cleanly extracted from raw files.
  - Look at the red warning box: **`RULE C5 • HIGH SEVERITY CONTRADICTION`**.
  - ProofPilot automatically caught that multiple charges shared the same transaction ID without a refund. The system saved the merchant from fighting a losing battle!

### Step 3: The Evidence-Grounded Draft
- Click the button **`2. Grounded Draft`** in the top action bar.
- Show the team the blue badges: `[Evidence E1]`, `[Evidence E3]`.
- **Interactive Feature:** Click on `[Evidence E1]`. Watch how the screen immediately scrolls and highlights Fact E1 on the left timeline!

### Step 4: The Issuer Red-Team & Human Signoff
- Click **`3. Issuer Red-Team`** $\rightarrow$ Show the adversarial bank weaknesses.
- Click **`4. Approve Response`** $\rightarrow$ Show the explicit human confirmation modal and reviewer signature.

---

## 🚀 Part 5: How We Make It Even Better (Our Building Phase Proposal)

Judges in the idea phase look for **depth, technical feasibility, and future vision**. Here is what we are proposing to build during the implementation phase:

### 1. Direct Webhook Integrations (Zero-Friction Ingestion)
- **Shopify & WooCommerce App:** Connect store with 1 click. When a chargeback occurs, ProofPilot pulls order history automatically.
- **Stripe & Adyen Webhooks:** Instantly notifies ProofPilot when a dispute is opened and automatically pushes the final approved response back to the processor API.
- **Logistics Connectors (FedEx / UPS / ShipStation):** Automatically fetches carrier GPS delivery scans and doorstep delivery photos.

### 2. Multi-Modal Vision & OCR for Physical Receipts
- Many retail & B2B merchants have paper delivery slips, signed bills of lading, or physical warehouse logs.
- We will integrate open-source vision models to extract structured facts directly from photos or PDF scans of paper receipts.

### 3. One-Click Visa & Mastercard Evidence Packet Compiler
- Automatically compile the approved letter, highlighted tracking scans, and accepted terms of service into a standardized **single-click PDF Evidence Packet** compliant with Visa Compelling Evidence 3.0 (CE 3.0) rules.

### 4. Enterprise Data Privacy & Local Edge LLMs
- Chargebacks contain sensitive customer financial data (names, billing addresses, last 4 digits of cards).
- ProofPilot is built to run on local open-source models (like **Llama 3.1 8B via Ollama**). We propose a zero-data-leakage architecture where **no customer data leaves the merchant's private server**.

---

## 📊 Part 6: Benchmark Proof (Our Experimental Results)

We ran ProofPilot against **50 seeded dispute cases** with a 20% holdout test split:

| Evaluation Metric | ProofPilot Result | Industry / Baseline Comparison |
| :--- | :--- | :--- |
| **Grounding Rate** | **100.0%** | Standard ChatGPT: $< 65\%$ (frequently hallucinated claims) |
| **Hallucinated Entities** | **0** | Target is 0 (No fake dates, amounts, or tracking numbers) |
| **Contradiction Recall** | **90.0%** | Successfully catches 9 out of 10 evidentiary conflicts |
| **ProofPilot Net P&L** | **\$0.00** | Protects capital by not contesting hopeless disputes |
| **Baseline: "Contest All"** | **-\$400.00** | Blindly contesting disputes incurs heavy \$40 fees on losing cases |
| **Net Value Added** | **+\$400.00** | ProofPilot saved \$400 in wasted fees on just 10 test disputes! |

---

## 🎯 Part 7: Hackathon Idea Submission Form (Draft Copy for Oct 23)

> 📋 *Here is the exact copy we can submit for our October 23 idea submission:*

- **Project Title:** ProofPilot — Evidence-Grounded AI Agent for Payment Dispute Response
- **Track:** Applied AI / Fintech / Autonomous Enterprise Workflows
- **Short Tagline:** *An AI copilot that turns messy evidence into bulletproof, economically verified chargeback responses with zero hallucinations.*
- **Problem Statement:** Online merchants lose \$100B+ yearly to payment disputes. Manually gathering evidence across shipping, order, and chat tools takes 45 minutes per dispute, and fighting weak cases incurs \$40 in non-refundable bank fees. Meanwhile, generative AI tools hallucinate fake dates and tracking numbers, resulting in instant losses.
- **Proposed Solution:** ProofPilot uses a specialized multi-pass agentic architecture:
  1. *Extraction:* Structures raw documents into an Evidence Graph.
  2. *Contradiction Engine:* Deterministic rules (C1–C6) detect physical data conflicts.
  3. *Economics Engine:* Calculates Net Expected Value to advise whether to Accept, Challenge, or Escalate.
  4. *Grounded Drafter & Verifier:* Enforces sentence-level citations with pure-code entity verification (0 hallucinations).
  5. *Issuer Red-Team:* Adversarially stress-tests defenses before submission.
  6. *Human-in-the-Loop:* Explicit confirmation ensuring no auto-submission.
- **Feasibility & Current Status:** We have already built an end-to-end working prototype (FastAPI backend with 30 passing unit/integration tests and React/TypeScript frontend) demonstrating a 100% grounding rate and \$400 net savings over standard baselines.

---

## 💬 Part 8: Open Discussion Points for the Team

Let's discuss these 3 questions today:
1. **Product Scope:** Should we focus our Phase 2 build on e-commerce (Shopify/Stripe) or B2B SaaS disputes?
2. **Feature Priority:** Which Phase 2 feature do we think judges will value most: the **Stripe webhook auto-sync** or the **Visa CE 3.0 PDF packet generator**?
3. **Roles for Phase 2:** Let's confirm team ownership:
   - *Lead / Product Pitch & Slide Deck*
   - *Backend & Rules Engine*
   - *Frontend & User Experience*
   - *Data, Benchmark & Integrations*

---

> 🚀 **Let's review the prototype and submit our proposal before October 23!**
