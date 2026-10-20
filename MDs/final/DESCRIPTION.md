Title: ProofPilot: Controlled-Autonomy Dispute Response Agent (Accept, Challenge or Escalate)

The problem

When a customer disputes a payment, a merchant has days to respond with proof scattered across order, courier, support and refund systems. Small teams spend time on cases that cost more to fight than they could recover, concede cases they could have won, and risk sending replies with unsupported or contradictory claims. Generic AI letter writers make the last problem worse by inventing details.

Our solution

ProofPilot is an agent that handles the dispute workflow end to end, not just the writing. For every incoming dispute it automatically:

Collects evidence and builds a timestamped Evidence Graph.
Detects contradictions and missing proof with deterministic rules (for example, delivery recorded before dispatch).
Calculates the estimated net value of contesting: (estimated win likelihood × recoverable amount) − (handling cost + fees).
Decides Accept, Challenge or Escalate, with plain-language reasons.
For challenges, drafts a response in which every sentence cites an evidence ID. A code-based verifier removes anything unsupported, and an adversarial review flags weak points.
Acts or escalates according to the merchant's policy, and logs every step in an audit trail.

Controlled autonomy: automation with limits

Case	What ProofPilot does
Uneconomic or confirmed merchant-error case under the merchant's cap	Accepts automatically
Well-evidenced case that passes verification and policy thresholds	Prepares the evidence packet and submits it automatically after a cancel window
Contradictions, missing proof, failed verification, high value or deadline risk	Stops and escalates to a person with the reasons and a ready draft

Merchant-set caps, hourly and daily exposure limits, a cancel window, a one-click kill switch and deadline timers bound every action. Decisions come from deterministic rules. The language model only reads documents and writes from verified facts. In the prototype, actions run against a simulated payment gateway.

What makes it different

It decides before it writes, so effort goes to cases worth fighting.
No evidence, no sentence: unsupported claims cannot reach a response.
Autonomy is bounded, explainable and auditable, not blind.

Example (illustrative numbers)

Three disputes arrive. A ₹650 duplicate charge is verified and accepted automatically. An ₹18,400 service dispute has usage logs, so the draft cites those logs, passes verification and is submitted after the cancel window. A ₹9,000 non-delivery dispute has a courier scan earlier than dispatch, so it is escalated with the contradiction highlighted.

What we will build and demonstrate

A simulated gateway that emits dispute events and accepts responses, with fixture-based order, courier and support data. Synthetic data only.
The Evidence Graph, contradiction rules, economics engine, policy engine, grounded drafting with verifier, cancel window, kill switch, audit log and a live case queue.
A template fallback if the model fails.
A benchmark of about 50 synthetic disputes against "contest everything" and "concede everything" baselines, plus tests for contradiction detection, unsupported claims and failure handling (duplicate events, model or connector outages).

Beyond the prototype

Live processor, Shopify, courier and chat integrations require merchant authorization and processor approval, so they are roadmap items. So is outcome-based calibration of the win estimate.

Expected impact

Less repetitive investigation, fewer uneconomic contests, more consistent and defensible responses, and human attention focused on real exceptions. We will report measured benchmark results, not projected savings.