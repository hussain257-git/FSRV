# Bank Fraud Investigation Assist (Multi-Agent Orchestration Prototype)

> **One-Line Goal:** A lightweight, high-performance prototype that automates fraud alert data gathering, unstructured notes synthesis, and policy-driven SOP decisioning so an investigator receives a consolidated, actionable case summary within seconds.

---

## 1. Problem Statement & Solution

### The Challenge
When an online banking fraud alert triggers (e.g., suspected Account Takeover, Card-Not-Present velocity, or Mule layering), investigators must manually navigate 6+ siloed banking systems (KYC core, transaction logs, dispute archives, investigator notes, and telephony logs) while cross-referencing complex Standard Operating Procedures (SOPs). This manual toil creates a **15 to 45 minute delay per case**, exposing the institution to fund exfiltration and creating customer friction.

### The Solution
A modular **Multi-Agent Cognitive Orchestrator** that executes parallel data gathering, unstructured NLP extraction, and policy rule evaluation, yielding an auditable, prioritized decision packet in **< 100 milliseconds** (well under the 3.0-second SLA).

---

## 2. Architecture & Data Flow

This prototype implements the **Case Assist Using Multi-Agentic AI** architecture:

```
                      +-------------------+
                      |   Risk Detected   |
                      +---------+---------+
                                | 1. Fraud Alert published
                                v
                   +------------+-------------+
       +---------> |  Case Orchestrator Agent | <---------+
       |           +---+-------------------+--+           |
       | 11. Fetch     | 2. Create         | 9. Update    | 12. Actions &
       |     Case      v    Case           v    Case      |     Decisions
+------+------+   +----+----+         +----+----+         |
|  PREVENT UI |   | Case DB |         | Case DB |   +-----+-----+
+------+------+   +---------+         +---------+   |  Analyst  |
       ^                                            +-----------+
       | 10. Pull Next Case                              |
       +-------------------------------------------------+
                                | 3. Trigger Offline
                                |    Agentic Investigation
                                v
                   +------------+-------------+
                   |   Investigation Agent    |
                   +--+-----+-------------+---+
                      |     |             |
     +----------------+     |             +-----------------+
     | 4. Profile           | 5. History                    | 6. Summarize
     v    Telemetry         v    Cases                      v    Notes
+----+--------+      +------+-------+             +---------+-----+
|    Cust     |      | Case History |             |     Notes     |
|  Profiling  |      |    Agent     |             | Summarization |
|    Agent    |      +------+-------+             |     Agent     |
+----+--------+             |                     +---------+-----+
     |                      |                               |
     +----------------------+-------------------------------+
                                    | 7. Evaluate SOPs
                                    v
                         +----------+----------+
                         |    Policy Decision  |
                         |        Agent        |
                         +---------------------+
                         - Red Flags / Violations
                         - Green Flags / Mitigations
                         - Recommended SOP Action
```

### Specialized Micro-Agents:
1. **Case Orchestrator Agent:** Ingests alerts, manages case lifecycle in Case DB, triggers asynchronous agentic investigation, aggregates outputs, and records immutable audit trail entries.
2. **Investigation Agent (Coordinator):** Orchestrates the parallel execution of the 3 data-gathering agents and synthesizes the consolidated summary and investigator call scripts.
3. **Cust Profiling Agent:** Queries simulated core banking telemetry (ECPR, OPS, DPMS, DCBS, TMS) to compute geolocation distance hops, spend deviation factor against 90-day baselines, and hardware device trust scores.
4. **Case History Agent:** Aggregates historical disputes, prior chargebacks, and previous false positive dispositions from CRA, Orig, and TFS.
5. **Notes Summarization Agent:** Synthesizes unstructured free-text investigator comments, customer care tickets, and Pindrop voice telephony acoustic biometrics into structured bullets, security events, and travel notifications.
6. **Policy Decision Agent:** Evaluates bank SOPs (OFD, ATO, EEDE, FPF, DTFR, RCDV) against the accumulated facts, producing auditable **Red Flags**, **Green Flags**, and prioritized actions.

---

## 3. Preloaded Fraud Scenarios

The prototype comes preloaded with four representative scenarios:

| Case ID | Scenario Type | Severity | Key Indicators | Recommended Action |
| :--- | :--- | :--- | :--- | :--- |
| **`CASE-ATO-8921`** | **Account Takeover (ATO)** | **CRITICAL** (Score: 98/100) | $14,500 wire to crypto exchange; foreign IP in Lagos, Nigeria (5,820 mi hop); headless browser; password reset 12h prior. | **🚫 Freeze Account & Revoke Credentials** |
| **`CASE-CNP-4402`** | **Card-Not-Present Spree** | **HIGH** (Score: 75/100) | 4 rapid digital gift card transactions in 5 min; commercial VPN proxy; past retail skimmer report in TFS. | **💳 Restrict Card / Suspend Transfers** |
| **`CASE-FP-1093`** | **Travel Exemption (False Positive)** | **LOW** (Score: 20/100) | $3,200 Paris hotel charge; **Green Flags:** customer travel notice on file, 99% FaceID biometric match, 52-month clean tenure. | **✓ Dismiss Alert (False Positive)** |
| **`CASE-ML-6718`** | **Money Mule / Rapid Layering** | **CRITICAL** (Score: 92/100) | Account age 2 months; immediate $9,850 crypto off-ramp 11 minutes after state disbursement; emulator detected. | **🚫 Freeze Account & Escalate to AML** |

---

## 4. Quickstart Guide

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Web browser (Chrome, Edge, Safari, Firefox)

### Installation
```bash
# 1. Clone or navigate to the project directory
cd fraud-investigation-assist

# 2. Install dependencies
python -m pip install -r requirements.txt
```

### Running the Prototype Server & UI
```bash
# Start the FastAPI application with live PREVENT UI
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser to:
- **PREVENT UI Dashboard:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive REST API Docs (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### Running All Automated Tests (Backend + Playwright UI):
```bash
python -m pytest tests/ -v
```

### Test Coverage Breakdown (19 Tests Passing):
- **`tests/test_enterprise_stack.py`**: Enterprise stack unit tests verifying:
  - `PIIMasker` redaction for PANs, SSNs, emails, phone numbers, account numbers, and ECNs.
  - `TachyonADKClientPool` token lifecycle, header auth, and model routing for `gpt5.1` and `gemini-2.5-pro`.
  - `EnterpriseDBManager` isolated multi-database connections (`case_context.db`, `sop_actions_2.db`, `policy_chat_history.db`).
  - `AuditStore` cryptographic SHA-256 hash chaining and tamper-evident verification.
  - `PolicyChatAgent` stateful conversation execution and context retrieval.
  - REST endpoints `POST /api/chat` and `GET /api/chat/{case_id}/history`.
- **`tests/test_agents.py`**: Unit tests verifying each micro-agent (Profiling, History, Notes, Policy) executes cleanly and generates valid Pydantic schemas.
- **`tests/test_policy_engine.py`**: Policy validation tests verifying that mitigating factors (travel notices + biometrics) produce Green Flags and calibrate risk scores down.
- **`tests/test_orchestrator.py`**: Performance and integration test verifying alert-to-summary turnaround is < 3.0s (measured at **< 30ms**).
- **`tests/test_api.py`**: REST API tests verifying case retrieval, analyst remediation action execution, and SLA metrics endpoints.
- **`tests/test_ui_playwright.py`**: End-to-end browser automation suite verifying:
  - PREVENT UI dashboard loading and online status indicators
  - Risk gauge rendering, headline, and Red/Green flag policy citations
  - Interactive tab navigation across all 6 sub-agent intelligence views
  - Full remediation action flow (Freeze Account & modal note capture)
  - Case queue prioritization and "Pull Next Case" button mechanics
  - Interactive Policy Chat tab with real-time prompt submission and Gemini 2.5 Pro streaming response

---

## 6. Enterprise Tech Stack Alignment

| Component | Enterprise Specification | Implementation in Prototype |
| :--- | :--- | :--- |
| **LLM Gateway** | Tachyon ADK Client Pool | `app/tachyon_client_pool.py`: Token refresh, bearer auth, multi-model routing |
| **Case History LLM** | `gpt5.1` | `app/agents/history_agent.py`: Stateless relationship evaluation via GPT-5.1 |
| **Policy Decision LLM** | `gpt5.1` | `app/agents/policy_agent.py`: Stateless parent decision evaluation via GPT-5.1 |
| **Policy Chat LLM** | `gemini-2.5-pro` | `app/agents/policy_chat.py`: Stateful Q&A reasoning via Gemini 2.5 Pro |
| **Privacy & Security** | Mandatory PII Masking | `app/masking.py`: Regex tokenization of PAN, SSN, email, phone, account, ECN |
| **Relational Stores** | Oracle connection pool (SQLite fallback) | `app/db.py`: `case_context.db`, `sop_actions_2.db`, `policy_chat_history.db` |
| **Audit Trail** | Append-only tamper-evident store | `app/audit_store.py`: Cryptographic SHA-256 hash chaining (`prev_hash` &rarr; `record_hash`) |
| **Investigator UI** | PREVENT UI Operations Console | Single-page responsive console with live Policy Chat tab (Tab 6) |
| **E2E Automation** | Playwright Test Suite | `tests/test_ui_playwright.py`: 6 automated browser scenarios in Chromium |

---

## 7. Demo Script for Interviews / Reviewers

1. **Open the PREVENT UI:**
   Show the clean, dark-mode financial crime operations dashboard (`http://127.0.0.1:8000`). Highlight the **Engine Online** indicator and the **SLA: < 3.0s** metric.
2. **Demonstrate "Pull Next Case":**
   Click **[Pull Next Case]** to load `CASE-ATO-8921`. Notice how the consolidated summary, 98/100 risk score, and headline populate immediately with a sub-second turnaround badge (`Turnaround: 24.8ms`).
3. **Show Red vs Green Flags:**
   Point out the Red Flags panel (`ATO-SOP-101`, `OFD-RULE-204`, `DTFR-RULE-305`) showing foreign IP mismatch and rapid password reset, alongside evidence pointers.
4. **Inspect Sub-Agent Tabs:**
   - Click **Cust Profiling Agent** to show the 5,820-mile geolocation distance hop and spend deviation factor.
   - Click **Notes Summarizer Agent** to show extracted Pindrop voice telephony warnings and CRM password reset logs.
   - Click **Policy Decision Agent** to view the exact SOP citation (`SOP-SEC-802`).
5. **Interact with Policy Chat (Gemini 2.5 Pro):**
   - Click tab **6. Policy Chat (Gemini 2.5 Pro)**.
   - Click a quick SOP query chip like *"SOP for ATO > $10k?"* or type *"Can I restrict card instead of freezing?"*.
   - Observe real-time policy reasoning citing `SOP-SEC-802`, explaining that restricting only the card leaves the wire channel vulnerable.
6. **Execute Remediation Action:**
   Click **[🚫 Freeze Account]**. In the modal, review the pre-populated SOP justification notes and click **Confirm & Execute**.
   Show how the status immediately updates to `RESOLVED BLOCKED` and the action is recorded with an immutable timestamp and SHA-256 hash in the **Audit Trail & Timeline** tab.
7. **Demonstrate False Positive Mitigation:**
   Select `CASE-FP-1093` (Dr. Jonathan Vance). Show how the system identified **Green Flags** (`GREEN-MIT-01`, `GREEN-MIT-02`) from the travel notice and biometric pass, successfully calibrating the risk score down to **20/100 (LOW)** and recommending **[✓ Dismiss Alert]**, preventing unnecessary account lockouts.
8. **Demonstrate Dynamic Alert Simulation:**
   Click **[Simulate Alert]**, select a scenario, and watch the orchestrator ingest the alert, dispatch agents, and update the queue in real-time.

