# 🚀 ProofPilot: Team Discussion & Hackathon Idea Submission Guide

> **Meeting Date:** October 20, 2026  
> **Submission Deadline:** October 23, 2026 (Idea Phase)  
> **Target Track:** Applied AI / Fintech / Autonomous Agents / Enterprise Automation  
> **Format:** Ready to import directly into **Notion** 📄

---

## 📌 Executive Summary (What to Tell Your Team in the First 60 Seconds)

> *"Hey team, online merchants lose **\$100+ Billion** every year to payment chargebacks and 'friendly fraud'. When a customer falsely claims they never got their item, banks give the merchant only a few days to gather proof across tracking logs, chats, and receipts. If the merchant fights a dispute with weak evidence, they lose an extra \$40 in non-refundable bank fees. If they use ChatGPT, the AI hallucinates fake tracking numbers and dates, which causes an instant loss.*
> 
> *We are submitting **ProofPilot**: an evidence-grounded AI copilot for merchant dispute response. It reads messy files, catches contradictions, runs an **Economics Engine** to ensure fighting is profitable, and enforces **'No evidence, no sentence'**—every claim links to real proof with 0 hallucinations. Even better: **we already built a working MVP and benchmark prototype**, which puts our idea miles ahead of competitors who only have slide decks."*

---

## ⏱️ Tomorrow's Team Meeting Agenda (25 Minutes)

| Time | Topic | Goal |
| :--- | :--- | :--- |
| **00 - 05m** | **The Problem & Market Opportunity** | Align on why chargebacks are a massive, painful problem for e-commerce. |
| **05 - 12m** | **Our Solution (ProofPilot)** | Walk through the 4-step pipeline: Extraction $\rightarrow$ Economics $\rightarrow$ Grounded Draft $\rightarrow$ Red-Team. |
| **12 - 17m** | **Live Demo / Working MVP** | Show the running React frontend & FastAPI backend to blow their minds. |
| **17 - 22m** | **How We Make It Better (Phase 2 Roadmap)** | Brainstorm extensions for the build phase (Stripe webhooks, OCR, etc.). |
| **22 - 25m** | **Submission Action Items (Due Oct 23)** | Finalize the submission copy and assign team ownership. |

---

## 🔍 Section 1: The Problem We Are Solving

### 1. The Real-World Pain Point
1. **The Chargeback Trap:**  
   When a customer claims *"I never got my box"* or *"I was billed twice"*, the card issuing bank (Chase, Citi, Amex) claws back the merchant's money immediately and adds a **\$25 non-refundable dispute fee**.
2. **Messy & Fragmented Evidence:**  
   Proof is scattered across 4–5 systems:
   - Courier logs (FedEx / UPS / DHL)
   - Order receipts (Shopify / WooCommerce)
   - Customer support chats (Zendesk / Gorgias)
   - Refund slips & merchant policies
3. **The Hidden Labor Cost:**  
   Investigating a dispute takes 30–45 minutes of manual employee time ($\approx \$15$ in labor). If a merchant fights a hopeless dispute, they lose:  
   $$\text{Disputed Amount} + \$25\text{ Bank Fee} + \$15\text{ Staff Labor} = \text{Total Loss}$$
4. **Why Generic AI (ChatGPT / Claude) Fails:**
   - **Hallucinations:** Large language models invent dates, guess tracking numbers, or make absolute claims (*"We guarantee delivery"*). In payment arbitration, **a single hallucinated entity causes an immediate loss**.
   - **No Unit Economics:** ChatGPT doesn't calculate whether a \$30 dispute is mathematically worth fighting.

---

## 💡 Section 2: Our Solution (ProofPilot)

ProofPilot bridges the gap between **unstructured evidence** and **strict financial/legal standards**:

```
[Messy Evidence: Courier Logs, Chats, Order Receipts, Policies]
                               │
                               ▼
            1. AI Fact Extractor (Structured Event Graph)
                               │
                               ▼
        2. Deterministic Contradiction Engine (Rules C1–C6)
                               │
                               ▼
        3. Economics Engine (Calculates Net Expected Value)
           Accept (Save Fees) | Challenge (Fight) | Escalate
                               │
                               ▼
      4. Grounded Drafter + Pure-Code Verifier ("No Evidence, No Sentence")
                               │
                               ▼
        5. Issuer Red-Team (Adversarial Stress Test)
                               │
                               ▼
        6. Human-in-the-Loop Signoff (Never Auto-Submits)
```

### Core Innovations Judges Will Love:
1. **The LLM Never Decides the Verdict:**  
   AI only does two things: *reads messy text* and *drafts human prose*. All financial math, win likelihood estimates, contradiction rules, and recommendations are handled by **100% deterministic code**.
2. **"No Evidence, No Sentence":**  
   Every sentence in the dispute letter has a clickable evidence badge (e.g., `[Evidence E1]`). A pure-code verifier checks that every date, dollar amount, and tracking ID exists verbatim in the source files. **Target: 0 hallucinations.**
3. **Adversarial Issuer Red-Team:**  
   A secondary AI agent roleplays as the bank's auditor, finding the top 3 weaknesses in the defense before the merchant submits it.
4. **Deadline-Aware Triage Queue:**  
   Ranks disputes by financial exposure and countdown urgency so merchants never miss strict bank deadlines.

---

## 🚀 Section 3: How Can It Get Better? (What to Propose for the Building Phase)

Judges in the idea phase want to know: *"If you get selected for the building phase, where will you take this project?"*

Here are the high-impact enhancements your team can propose for Phase 2:

### 1. Real-World Ingestion & Integrations
- **1-Click Platform Integrations:** Webhook connectors for **Shopify**, **WooCommerce**, and **Stripe** to pull disputes automatically the second they are filed.
- **Logistics APIs:** Direct API integration with **FedEx**, **UPS**, and **ShipStation** to auto-fetch GPS delivery coordinates and photo delivery proof.
- **Support Desk Connectors:** Auto-pull chat transcripts from **Zendesk** and **Gorgias**.

### 2. Multi-Modal Vision & OCR
- Extract structured facts directly from **scanned paper delivery receipts, bills of lading, and signature pads** using lightweight open-source vision models.

### 3. Automated Visa/Mastercard Packet Generator
- Compile the approved grounded draft, annotated tracking screenshots, and highlighted terms into a standardized **single-click PDF Evidence Packet** formatted to Visa CE 3.0 and Mastercard dispute standards.

### 4. Smart Policy Learning (Merchant Memory)
- Learn from historical merchant wins/losses to dynamically tune playbook evidence weights per store without retraining models.

### 5. Private / On-Premise Local LLM Deployment
- Run entirely on local company servers using quantized open-source models (Llama 3.1 8B via Ollama) with **zero customer data leaving the merchant's network** (crucial for enterprise privacy & GDPR).

---

## 🏆 Section 4: Our Unfair Advantage for the Hackathon

Most teams submitting on October 23 will only have a PDF pitch deck or Figma mockups. 

**Our team already has a functional, fully tested MVP ready to demonstrate:**
- ✅ **FastAPI Backend** with 30/30 passing pytest unit and integration tests.
- ✅ **React + TypeScript + Tailwind CSS Frontend** with interactive timeline, clickable evidence chips, triage queue, and audit trail.
- ✅ **Deterministic Rules Engine (C1–C6)** catching real contradictions.
- ✅ **Benchmark Suite** run on 50 synthetic dispute cases showing:
  - **Grounding Rate:** 100.0%
  - **Hallucinated Entities:** 0 (Dates, amounts, tracking IDs)
  - **Contradiction Recall:** 90.0%
  - **Net Value Added vs "Contest All":** +\$400.00 saved on 10 holdout cases.
- ✅ **Zero Cost:** Works 100% offline with zero paid API dependencies.

---

## 📝 Section 5: Ready-to-Submit Hackathon Idea Template

Use this text directly (or adapt it) for your **October 23 idea submission form**:

### Project Name
**ProofPilot — Evidence-Grounded AI Agent for Payment Dispute Response**

### One-Line Tagline
*An AI copilot that turns messy evidence into bulletproof, economically verified chargeback responses with zero hallucinations.*

### The Problem
Online merchants lose over \$100B annually to chargebacks. Responding to disputes is a manual operational nightmare: evidence is fragmented across logistics logs, customer chats, and order receipts. Merchants frequently lose \$40 in non-refundable bank fees by contesting disputes they cannot win. Meanwhile, generic LLMs (like ChatGPT) cannot be trusted because they hallucinate fake dates, amounts, and tracking numbers, which triggers instant arbitration loss.

### Our Solution
ProofPilot combines applied AI with deterministic verification and financial modeling:
1. **Extraction:** An LLM structures raw documents into an Evidence Graph of verified facts.
2. **Contradiction Detection:** Deterministic rules detect physical impossibilities (e.g. delivery before dispatch, address mismatches).
3. **Economics Engine:** Calculates the Net Expected Value ($\text{Net EV}$) of contesting vs accepting. If fees exceed expected recovery, it recommends conceding to preserve capital.
4. **Grounded Drafting:** Generates dispute letters where every claim is backed by cited evidence ("No evidence, no sentence"). A pure-code verifier ensures zero hallucinations.
5. **Issuer Red-Team:** An adversarial AI roleplays as the bank auditor to surface vulnerabilities.
6. **Human-in-the-Loop:** An authorized human reviews and signs off; the system never auto-submits.

### Technical Architecture
- **Backend:** Python 3.12, FastAPI, Pydantic v2, SQLite (stdlib `sqlite3`).
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS.
- **AI / LLM:** Hybrid architecture supporting local open-source models (Llama 3.1 8B via Ollama) and deterministic mock fixtures for 100% offline, zero-cost execution.
- **Safety & Verification:** Pure-code entity verifier (regex + fact corpus) + append-only audit trail.

### Key Metrics & Feasibility Proof
Our initial prototype benchmarked against 50 dispute cases demonstrates:
- **100% Grounding Verification Rate** with **0 Hallucinations**.
- **+\$400 Net Value Added** over standard "contest everything" merchant behavior.
- **Fully working prototype** already implemented with 30 passing integration/unit tests.

---

## 👥 Section 6: Team Roles & Work Allocation (Building Phase)

To present a unified team front, assign these ownership areas:

| Member / Role | Responsibility | Key Deliverables |
| :--- | :--- | :--- |
| **Lead / Product & Strategy** | Project narrative, pitch presentation, business economics, demo video. | Slide deck, pitch script, benchmark storytelling. |
| **Backend & AI Engineer** | FastAPI endpoints, Ollama/LLM prompt tuning, verifier logic, database schema. | API routes, contradiction rules, red-team loop. |
| **Frontend & UI Engineer** | React components, Tailwind styling, interactive evidence chip highlighting. | Triage Queue UX, Case Workspace, responsive design. |
| **Data & Integrations Engineer** | Test split dataset, synthetic case generation, benchmark metrics, webhook mocks. | Stripe/Shopify mock payloads, evaluation charts. |

---

## ❓ Section 7: Anticipated Team Questions & Answers

### Q1: *"Do we need to pay for OpenAI API keys or GPU servers?"*
> **Answer:** **No, cost is \$0.** ProofPilot is architected to run with zero paid APIs. For testing and demos, it uses a deterministic mock engine, and for live AI, it connects to open-source models (like Llama 3.1) running locally through Ollama.

### Q2: *"Is our prototype already too complete for an idea phase?"*
> **Answer:** Having working code in the idea phase is the **single highest predictor of qualifying**. Hackathon judges evaluate "Feasibility" and "Execution Capability". Showing that we already proved the core concept and have a clear vision for Phase 2 (Shopify/Stripe webhooks, OCR, Visa packet generation) makes our submission practically unbeatable.

### Q3: *"What should our live demo look like during the pitch?"*
> **Answer:** A quick 90-second run:
> 1. Show the **Triage Queue** with deadline countdowns.
> 2. Open `CASE-0029` with the high-severity duplicate charge contradiction.
> 3. Click **"Grounded Draft"** and click a blue `[Evidence E1]` chip to show it highlighting the source document.
> 4. Click **"Issuer Red-Team"** to show the adversarial bank feedback.
> 5. Click **"Approve"** to show the human governance confirmation modal.

---

> 💡 **Next Step:** Copy this file into Notion or your team's workspace, review it before tomorrow's meeting, and submit the proposal before October 23!
