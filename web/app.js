// PREVENT UI — Bank Fraud Investigation Assist Client Logic
let currentCases = [];
let activeCase = null;
let currentFilter = "ALL";
let pendingActionType = null;

// DOM Elements
const caseListContainer = document.getElementById("case-list-container");
const queueCountEl = document.getElementById("queue-count");
const btnPullNext = document.getElementById("btn-pull-next");
const btnSimulate = document.getElementById("btn-simulate");
const btnReset = document.getElementById("btn-reset");
const filterChips = document.querySelectorAll(".filter-chip");
const tabButtons = document.querySelectorAll(".tab-btn");
const tabPanes = document.querySelectorAll(".tab-pane");

// Modal Elements
const actionModal = document.getElementById("action-modal");
const modalActionTitle = document.getElementById("modal-action-title");
const modalActionDesc = document.getElementById("modal-action-desc");
const modalNotes = document.getElementById("modal-notes");
const btnModalConfirm = document.getElementById("btn-modal-confirm");
const btnModalCancel = document.getElementById("btn-modal-cancel");
const btnModalClose = document.getElementById("btn-modal-close");

const simModal = document.getElementById("sim-modal");
const btnSimCancel = document.getElementById("btn-sim-cancel");
const btnSimClose = document.getElementById("btn-sim-close");
const simCards = document.querySelectorAll(".sim-card");

// Chat Elements
let chatMessagesContainer;
let chatInputForm;
let chatUserInput;
let chatSendBtn;
let quickChips;

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  chatMessagesContainer = document.getElementById("chat-messages-container");
  chatInputForm = document.getElementById("chat-input-form");
  chatUserInput = document.getElementById("chat-user-input");
  chatSendBtn = document.getElementById("chat-send-btn");
  quickChips = document.querySelectorAll(".quick-chip");

  fetchCases();
  setupEventListeners();
});

function setupEventListeners() {
  // Pull next case
  btnPullNext.addEventListener("click", pullNextCase);

  // Re-orchestrate reset
  btnReset.addEventListener("click", resetAllCases);

  // Simulate modal
  btnSimulate.addEventListener("click", () => simModal.classList.remove("hidden"));
  btnSimCancel.addEventListener("click", () => simModal.classList.add("hidden"));
  btnSimClose.addEventListener("click", () => simModal.classList.add("hidden"));

  simCards.forEach((card) => {
    card.addEventListener("click", () => {
      const idx = parseInt(card.getAttribute("data-scenario"), 10);
      simulateAlert(idx);
      simModal.classList.add("hidden");
    });
  });

  // Action modal controls
  btnModalCancel.addEventListener("click", () => actionModal.classList.add("hidden"));
  btnModalClose.addEventListener("click", () => actionModal.classList.add("hidden"));
  btnModalConfirm.addEventListener("click", confirmAndExecuteAction);

  // Queue filter chips
  filterChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      filterChips.forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      currentFilter = chip.getAttribute("data-filter");
      renderQueue();
    });
  });

  // Tabs
  const allTabButtons = document.querySelectorAll(".tab-btn");
  const allTabPanes = document.querySelectorAll(".tab-pane");
  allTabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetTabId = btn.getAttribute("data-tab");
      allTabButtons.forEach((b) => b.classList.remove("active"));
      allTabPanes.forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      const targetEl = document.getElementById(targetTabId);
      if (targetEl) targetEl.classList.add("active");
    });
  });

  // Policy Chat Form Submit
  if (chatInputForm) {
    chatInputForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const text = chatUserInput.value.trim();
      if (text) {
        sendChatMessage(text);
      }
    });
  }

  // Quick Chat Prompt Chips
  quickChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const promptText = chip.getAttribute("data-prompt");
      if (promptText) {
        if (chatUserInput) chatUserInput.value = promptText;
        sendChatMessage(promptText);
      }
    });
  });

  // Action decision buttons
  const actionBtns = document.querySelectorAll(".btn-action");
  actionBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const actionType = btn.getAttribute("data-action");
      openActionModal(actionType);
    });
  });

  // Audio Text-to-Speech for Customer Call Script
  const btnSpeak = document.getElementById("btn-speak-script");
  if (btnSpeak) {
    btnSpeak.addEventListener("click", toggleSpeakScript);
  }

  // Copy 1930 Cyber Fraud Incident Dossier
  const btnCopyDossier = document.getElementById("btn-copy-dossier");
  if (btnCopyDossier) {
    btnCopyDossier.addEventListener("click", copyCyberFraudDossier);
  }
}

// Indian Rupee (INR) Formatting with Lakhs/Crores syntax
function formatINR(amount) {
  if (amount === null || amount === undefined) return "₹0.00";
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2
  }).format(amount);
}

// Fetch all cases from API
async function fetchCases(selectCaseId = null) {
  try {
    const res = await fetch("/api/cases");
    if (!res.ok) throw new Error("Failed to load cases");
    currentCases = await res.json();
    renderQueue();

    if (currentCases.length > 0) {
      if (selectCaseId) {
        const found = currentCases.find((c) => c.case_id === selectCaseId);
        selectCase(found || currentCases[0]);
      } else if (!activeCase) {
        selectCase(currentCases[0]);
      } else {
        // Refresh active case data
        const currentFound = currentCases.find((c) => c.case_id === activeCase.case_id);
        if (currentFound) selectCase(currentFound);
      }
    }
  } catch (err) {
    console.error("Error fetching cases:", err);
  }
}

// Pull Next Case
async function pullNextCase() {
  try {
    const res = await fetch("/api/cases/next");
    if (!res.ok) throw new Error("No unreviewed cases");
    const nextCase = await res.json();
    selectCase(nextCase);
  } catch (err) {
    console.warn("Pull next fallback:", err);
    if (currentCases.length > 0) selectCase(currentCases[0]);
  }
}

// Simulate Alert Ingestion
async function simulateAlert(scenarioIndex) {
  try {
    const res = await fetch("/api/cases/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario_index: scenarioIndex }),
    });
    if (!res.ok) throw new Error("Failed to simulate alert");
    const newCase = await res.json();
    await fetchCases(newCase.case_id);
  } catch (err) {
    console.error("Simulation error:", err);
  }
}

// Reset all cases
async function resetAllCases() {
  try {
    const res = await fetch("/api/cases/reset-all", { method: "POST" });
    if (!res.ok) throw new Error("Failed to reset");
    await fetchCases();
  } catch (err) {
    console.error("Reset error:", err);
  }
}

// Render Queue List
function renderQueue() {
  caseListContainer.innerHTML = "";
  
  let filtered = currentCases;
  if (currentFilter === "READY") {
    filtered = currentCases.filter((c) => c.status === "READY_FOR_REVIEW" || c.status === "UNDER_INVESTIGATION");
  } else if (currentFilter === "RESOLVED") {
    filtered = currentCases.filter((c) => c.status.startsWith("RESOLVED") || c.status === "ESCALATED");
  }

  queueCountEl.textContent = filtered.length;

  filtered.forEach((c) => {
    const item = document.createElement("div");
    item.className = `case-list-item ${activeCase && activeCase.case_id === c.case_id ? "selected" : ""}`;
    
    const severity = c.policy_result ? c.policy_result.risk_level.toLowerCase() : "medium";
    const amount = c.alert ? formatINR(c.alert.trigger_transaction.amount) : "₹0.00";
    const customer = c.customer_profile ? c.customer_profile.full_name : "Unknown Customer";

    item.innerHTML = `
      <div class="item-top">
        <span class="item-id">${c.case_id}</span>
        <span class="item-badge ${severity}">${c.alert.alert_type}</span>
      </div>
      <div class="item-name">${customer}</div>
      <div class="item-meta">
        <span>${c.status.replace("_", " ")}</span>
        <strong class="font-mono">${amount}</strong>
      </div>
    `;

    item.addEventListener("click", () => selectCase(c));
    caseListContainer.appendChild(item);
  });
}

// Select Case and populate view
function selectCase(c) {
  activeCase = c;
  renderQueue();

  // Populate Banner
  document.getElementById("case-id-title").textContent = c.case_id;
  document.getElementById("case-alert-type").textContent = c.alert.alert_type;
  document.getElementById("case-status-badge").textContent = c.status.replace(/_/g, " ");
  document.getElementById("case-trigger-reason").textContent = c.alert.trigger_reason;

  const durationMs = c.investigation_duration_ms || 24.8;
  document.getElementById("case-latency-badge").textContent = `Turnaround: ${durationMs.toFixed(1)}ms`;

  const riskScore = c.policy_result ? c.policy_result.risk_score : c.alert.initial_risk_score;
  const riskLevel = c.policy_result ? c.policy_result.risk_level : "MEDIUM";

  document.getElementById("risk-score-num").textContent = riskScore;
  const pill = document.getElementById("risk-severity-pill");
  pill.textContent = `${riskLevel} RISK`;
  pill.className = `risk-severity-pill ${riskLevel.toLowerCase()}`;

  // Metadata Strip (Indian Banking context)
  document.getElementById("meta-customer-name").textContent = c.customer_profile.full_name;
  document.getElementById("meta-account-num").textContent = c.customer_profile.account_number;
  document.getElementById("meta-tx-amount").textContent = `${formatINR(c.alert.trigger_transaction.amount)} INR`;
  document.getElementById("meta-channel").textContent = `${c.alert.trigger_transaction.channel} (${c.alert.trigger_transaction.merchant_name})`;
  document.getElementById("meta-location").textContent = `${c.alert.device_telemetry.city}, ${c.alert.device_telemetry.country} ${c.alert.device_telemetry.is_vpn_or_proxy ? '(Proxy/VPN)' : ''}`;
  document.getElementById("meta-home").textContent = `${c.customer_profile.registered_city}, ${c.customer_profile.registered_state}`;

  // Render Live Precursor Transaction Sequence & Geo Route
  renderTransactionStream(c);

  // Consolidated Summary
  if (c.consolidated_summary) {
    document.getElementById("summary-headline").textContent = c.consolidated_summary.headline;
    document.getElementById("summary-assessment").textContent = c.consolidated_summary.risk_assessment;
    document.getElementById("summary-confidence").textContent = `Confidence: ${(c.consolidated_summary.confidence_score * 100).toFixed(0)}%`;

    const findingsList = document.getElementById("summary-findings-list");
    findingsList.innerHTML = c.consolidated_summary.key_findings.map((f) => `<li>${f}</li>`).join("");

    const stepsList = document.getElementById("summary-steps-list");
    stepsList.innerHTML = c.consolidated_summary.next_step_plan.map((s) => `<li>${s}</li>`).join("");

    document.getElementById("summary-script").textContent = c.consolidated_summary.suggested_investigator_script || "No specific verbal verification script required for this scenario.";
  }

  // Red & Green Flags
  const redFlags = (c.policy_result && c.policy_result.red_flags) || [];
  const greenFlags = (c.policy_result && c.policy_result.green_flags) || [];

  document.getElementById("red-flags-count").textContent = redFlags.length;
  document.getElementById("green-flags-count").textContent = greenFlags.length;

  const redContainer = document.getElementById("red-flags-container");
  if (redFlags.length === 0) {
    redContainer.innerHTML = `<div class="flag-desc">No red flags triggered under SOP policy rules.</div>`;
  } else {
    redContainer.innerHTML = redFlags.map((rf) => `
      <div class="flag-item red-item">
        <div class="flag-item-top">
          <span class="flag-name">${rf.flag_name}</span>
          <span class="flag-rule-id">${rf.rule_id}</span>
        </div>
        <div class="flag-desc">${rf.description}</div>
        <div class="flag-evidence">Evidence: ${rf.evidence_pointer}</div>
      </div>
    `).join("");
  }

  const greenContainer = document.getElementById("green-flags-container");
  if (greenFlags.length === 0) {
    greenContainer.innerHTML = `<div class="flag-desc">No mitigating factors identified.</div>`;
  } else {
    greenContainer.innerHTML = greenFlags.map((gf) => `
      <div class="flag-item green-item">
        <div class="flag-item-top">
          <span class="flag-name">${gf.flag_name}</span>
          <span class="flag-rule-id">${gf.rule_id}</span>
        </div>
        <div class="flag-desc">${gf.description}</div>
        <div class="flag-evidence">Evidence: ${gf.evidence_pointer}</div>
      </div>
    `).join("");
  }

  // Profiling Tab
  if (c.profiling_result) {
    document.getElementById("prof-spend-dev").textContent = `${c.profiling_result.spend_deviation_factor.toFixed(1)}x`;
    document.getElementById("prof-geo-dist").textContent = `${c.profiling_result.geolocation_distance_miles.toLocaleString()} mi`;
    document.getElementById("prof-device-trust").textContent = `${(c.profiling_result.device_trust_score * 100).toFixed(0)}%`;
    document.getElementById("prof-tenure").textContent = `${c.profiling_result.tenure_months} mos`;
    document.getElementById("prof-summary-text").textContent = c.profiling_result.profiling_summary;

    const sysContainer = document.getElementById("profiling-systems");
    sysContainer.innerHTML = c.profiling_result.linked_systems_consulted
      .map((s) => `<span class="system-chip">${s}</span>`)
      .join("");
  }

  // History Tab
  if (c.history_result) {
    document.getElementById("history-summary-text").textContent = c.history_result.account_relationship_summary;
    const histTable = document.getElementById("history-table-body");
    if (c.history_result.recent_cases.length === 0) {
      histTable.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-dim);">No prior disputes or fraud cases recorded in CRA/TFS.</td></tr>`;
    } else {
      histTable.innerHTML = c.history_result.recent_cases.map((h) => `
        <tr>
          <td class="font-mono">${h.case_id}</td>
          <td>${h.date}</td>
          <td>${h.alert_type}</td>
          <td><span class="item-badge ${h.disposition.includes('FRAUD') ? 'critical' : 'low'}">${h.disposition}</span></td>
          <td class="font-mono">${formatINR(h.loss_amount_usd)}</td>
          <td>${h.summary}</td>
        </tr>
      `).join("");
    }

    const histSys = document.getElementById("history-systems");
    histSys.innerHTML = c.history_result.systems_consulted
      .map((s) => `<span class="system-chip">${s}</span>`)
      .join("");
  }

  // Notes Tab
  if (c.notes_result) {
    const notesBullets = document.getElementById("notes-bullets-list");
    notesBullets.innerHTML = c.notes_result.bullet_points.map((bp) => `<li>${bp}</li>`).join("");

    const badge = document.getElementById("notes-sentiment-badge");
    badge.textContent = `Sentiment: ${c.notes_result.customer_sentiment}`;

    const notesSys = document.getElementById("notes-systems");
    notesSys.innerHTML = c.notes_result.systems_consulted
      .map((s) => `<span class="system-chip">${s}</span>`)
      .join("");
  }

  // Policy Tab
  if (c.policy_result) {
    document.getElementById("policy-pack-name").textContent = c.policy_result.policy_pack;
    document.getElementById("policy-rec-action").textContent = `${c.policy_result.recommended_action} — ${c.policy_result.recommended_action_title}`;
    document.getElementById("policy-urgency").textContent = c.policy_result.action_urgency;
    document.getElementById("policy-sop-ref").textContent = c.policy_result.sop_reference;
    document.getElementById("policy-alternatives").textContent = c.policy_result.alternative_actions.join(", ");
  }

  // Audit Tab
  const timeline = document.getElementById("audit-timeline");
  timeline.innerHTML = (c.audit_trail || []).map((entry) => {
    const timeStr = new Date(entry.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 });
    return `
      <div class="timeline-item">
        <div class="timeline-item-header">
          <span class="timeline-time">${timeStr}</span>
          <span class="timeline-actor">[${entry.actor}]</span>
          <span class="timeline-action">${entry.action}</span>
        </div>
        <div class="timeline-details">${entry.details}</div>
      </div>
    `;
  }).join("");

  // Load Policy Chat History for this case
  loadChatHistory(c.case_id);
}

// Open Action Modal
function openActionModal(actionType) {
  if (!activeCase) return;
  pendingActionType = actionType;

  const actionTitles = {
    BLOCK_ACCOUNT: "Freeze Account & Revoke Online Credentials",
    RESTRICT_CARD: "Place Temporary Restriction on Debit Card",
    CONTACT_CUSTOMER: "Initiate Customer Outreach & Identity Verification",
    ESCALATE_TIER2: "Escalate Case to Tier 2 Financial Crimes / AML",
    DISMISS_FALSE_POSITIVE: "Dismiss Alert as Verified Legitimate Activity (False Positive)",
  };

  modalActionTitle.textContent = actionTitles[actionType] || actionType;
  modalActionDesc.textContent = `You are executing ${actionType} on Case ${activeCase.case_id} (${activeCase.customer_profile.full_name}). This action is recorded permanently in the audit trail.`;

  // Default notes suggestion
  if (actionType === "BLOCK_ACCOUNT") {
    modalNotes.value = "Confirmed severe credential compromise and foreign wire exfiltration. Freezing account per SOP-SEC-802.";
  } else if (actionType === "DISMISS_FALSE_POSITIVE") {
    modalNotes.value = "Customer travel notification confirmed with verified biometric match. Authorized charge cleared.";
  } else {
    modalNotes.value = `Action executed per SOP recommendation: ${actionType}.`;
  }

  actionModal.classList.remove("hidden");
}

// Confirm and Execute Action
async function confirmAndExecuteAction() {
  if (!activeCase || !pendingActionType) return;
  const notes = modalNotes.value.trim() || "Investigator reviewed and approved action.";

  try {
    const res = await fetch(`/api/cases/${activeCase.case_id}/actions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action_type: pendingActionType,
        analyst_id: "OFD-ANALYST-409",
        analyst_name: "Sarah Jenkins",
        investigator_notes: notes,
      }),
    });

    if (!res.ok) throw new Error("Failed to execute action");
    actionModal.classList.add("hidden");
    await fetchCases(activeCase.case_id);
  } catch (err) {
    console.error("Action execution error:", err);
    alert(`Error executing action: ${err.message}`);
  }
}

// ==========================================================================
// Policy Chat Functions (Gemini 2.5 Pro via Tachyon ADK)
// ==========================================================================

async function loadChatHistory(caseId) {
  if (!chatMessagesContainer) return;
  chatMessagesContainer.innerHTML = "";

  try {
    const res = await fetch(`/api/chat/${caseId}/history`);
    if (!res.ok) throw new Error("Failed to load chat history");
    const messages = await res.json();

    if (!messages || messages.length === 0) {
      chatMessagesContainer.innerHTML = `
        <div class="chat-empty-state">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
          <strong style="color: var(--text-main); font-size: 14px;">OFD Policy Assistant Ready</strong>
          <p style="font-size: 12px; max-width: 360px;">Ask any question regarding bank SOP policies, exemption rules, or verification procedures for <strong>${caseId}</strong>.</p>
        </div>
      `;
      return;
    }

    messages.forEach((msg) => {
      renderChatMessage(msg.sender, msg.content, msg.timestamp, msg.model_used);
    });

    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
  } catch (err) {
    console.error("Failed to load chat history:", err);
    chatMessagesContainer.innerHTML = `<div class="chat-empty-state"><p>Unable to load chat history for this case.</p></div>`;
  }
}

function renderChatMessage(sender, content, timestamp, modelUsed = null) {
  if (!chatMessagesContainer) return;

  // Remove empty state if present
  const emptyState = chatMessagesContainer.querySelector(".chat-empty-state");
  if (emptyState) emptyState.remove();

  const isAnalyst = sender === "analyst" || sender === "ANALYST";
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${isAnalyst ? "analyst" : "agent"}`;

  const timeStr = timestamp ? new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : "";
  const senderLabel = isAnalyst ? "Investigator (Analyst)" : "Policy Assistant";
  const modelTag = (!isAnalyst && modelUsed) ? `<span class="chat-badge-pill">${modelUsed}</span>` : "";

  bubble.innerHTML = `
    <div class="chat-bubble-header">
      <span class="chat-sender-badge">
        ${isAnalyst ? '👤' : '🤖'} ${senderLabel} ${modelTag}
      </span>
      <span class="font-mono text-xs">${timeStr}</span>
    </div>
    <div class="chat-bubble-content">${formatChatContent(content)}</div>
  `;

  chatMessagesContainer.appendChild(bubble);
  chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
}

function formatChatContent(content) {
  if (!content) return "";
  // Escape HTML tags to prevent XSS
  const div = document.createElement("div");
  div.textContent = content;
  let text = div.innerHTML;

  // Bold SOP references like SOP-SEC-802 or SOP-EXEMP-105
  text = text.replace(/(SOP-[A-Z0-9\-]+)/g, "<strong style='color:#93c5fd;'>$1</strong>");
  return text;
}

async function sendChatMessage(userText) {
  if (!activeCase || !userText.trim()) return;

  const nowIso = new Date().toISOString();
  renderChatMessage("analyst", userText, nowIso);

  if (chatUserInput) chatUserInput.value = "";
  if (chatSendBtn) chatSendBtn.disabled = true;

  // Show typing indicator
  const indicator = document.createElement("div");
  indicator.className = "typing-indicator";
  indicator.id = "chat-typing-indicator";
  indicator.innerHTML = "<span></span><span></span><span></span>";
  chatMessagesContainer.appendChild(indicator);
  chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ai_case_id: activeCase.case_id,
        message: userText
      })
    });

    if (!res.ok) {
      throw new Error(`Chat API error: ${res.statusText}`);
    }

    const data = await res.json();
    indicator.remove();
    renderChatMessage(data.sender, data.content, data.timestamp, data.model_used);
  } catch (err) {
    console.error("Chat send error:", err);
    indicator.remove();
    renderChatMessage("policy_chat_agent", `Error: Failed to obtain policy guidance (${err.message}).`, new Date().toISOString(), "gemini-2.5-pro");
  } finally {
    if (chatSendBtn) chatSendBtn.disabled = false;
    if (chatUserInput) chatUserInput.focus();
  }
}

// ==========================================================================
// Transaction Velocity Stream & Audio Synthesis Enhancements
// ==========================================================================

function renderTransactionStream(c) {
  const container = document.getElementById("txn-sequence-container");
  const geoRouteEl = document.getElementById("geo-route-pill");
  if (!container) return;

  const isLow = (c.policy_result && c.policy_result.risk_level === "LOW");
  const distKm = c.profiling_result ? Math.round(c.profiling_result.geolocation_distance_miles * 1.609) : 0;

  if (geoRouteEl) {
    geoRouteEl.className = `geo-route-pill ${isLow ? 'low' : ''}`;
    geoRouteEl.textContent = `📍 ${c.customer_profile.registered_city} (Home) ➔ ${c.alert.device_telemetry.city} (${c.alert.device_telemetry.country}) • ${distKm.toLocaleString()} km ${isLow ? '(Verified Travel / Local)' : '(Velocity Anomaly)'}`;
  }

  // Precursor transactions generated based on case context
  let precursors = [];
  const trig = c.alert.trigger_transaction;

  if (c.alert.alert_type === "UPI_SCAM") {
    precursors = [
      { time: "12:55:10", chan: "UPI", chanClass: "upi", amount: 1.00, desc: "BillDesk UPI Micro-Auth", status: "CLEARED" },
      { time: "13:10:20", chan: "UPI", chanClass: "upi", amount: 2000.00, desc: "QuickSupport Screen Test", status: "SUSPICIOUS" },
      { time: "13:14:55", chan: "UPI", chanClass: "upi", amount: trig.amount, desc: trig.merchant_name, status: "CRITICAL TRIGGER", isTrigger: true }
    ];
  } else if (c.alert.alert_type === "SIM_SWAP") {
    precursors = [
      { time: "11:00:00", chan: "TEL", chanClass: "aeps", amount: 0.00, desc: "e-SIM Swap Carrier Callback", status: "SECURITY_FLAG" },
      { time: "13:42:15", chan: "IMPS", chanClass: "imps", amount: 1000.00, desc: "Beneficiary Add Test", status: "FLAGGED" },
      { time: "14:01:40", chan: "RTGS", chanClass: "rtgs", amount: trig.amount, desc: trig.merchant_name, status: "CRITICAL TRIGGER", isTrigger: true }
    ];
  } else if (c.alert.alert_type === "AEPS_SPOOF") {
    precursors = [
      { time: "15:02:10", chan: "AEPS", chanClass: "aeps", amount: 10000.00, desc: "Purnia CSP Micro-ATM Attempt 1", status: "FLAGGED" },
      { time: "15:06:22", chan: "AEPS", chanClass: "aeps", amount: 10000.00, desc: "Purnia CSP Micro-ATM Attempt 2", status: "FLAGGED" },
      { time: "15:10:10", chan: "AEPS", chanClass: "aeps", amount: trig.amount, desc: trig.merchant_name, status: "CRITICAL TRIGGER", isTrigger: true }
    ];
  } else if (c.alert.alert_type === "TRAVEL_SUSPICION") {
    precursors = [
      { time: "09:30:15", chan: "POS", chanClass: "upi", amount: 450.00, desc: "Blue Tokai Coffee (Delhi)", status: "CLEARED" },
      { time: "10:15:00", chan: "UPI", chanClass: "upi", amount: 1200.00, desc: "Uber Delhi Airport", status: "CLEARED" },
      { time: "11:04:45", chan: "POS", chanClass: "upi", amount: trig.amount, desc: trig.merchant_name, status: "VERIFIED GENUINE", isTrigger: true }
    ];
  } else {
    // Standard ATO or CNP
    precursors = [
      { time: "01:45:10", chan: "NET", chanClass: "imps", amount: 0.00, desc: "NetBanking Password Reset", status: "OFF-HOURS" },
      { time: "08:10:00", chan: "IMPS", chanClass: "imps", amount: 500.00, desc: "Test Beneficiary Transfer", status: "SUSPICIOUS" },
      { time: "08:14:15", chan: trig.channel, chanClass: "imps", amount: trig.amount, desc: trig.merchant_name, status: "CRITICAL TRIGGER", isTrigger: true }
    ];
  }

  container.innerHTML = precursors.map((p) => `
    <div class="txn-seq-card ${p.isTrigger ? 'trigger-txn' : ''}">
      <div class="txn-seq-top">
        <span>🕒 ${p.time}</span>
        <span class="channel-tag ${p.chanClass}">${p.chan}</span>
      </div>
      <div class="txn-seq-amount">${formatINR(p.amount)}</div>
      <div class="txn-seq-desc" title="${p.desc}">${p.desc}</div>
    </div>
  `).join("");
}

let speechUtterance = null;
function toggleSpeakScript() {
  const btnSpeak = document.getElementById("btn-speak-script");
  const scriptEl = document.getElementById("summary-script");
  if (!scriptEl || !('speechSynthesis' in window)) {
    alert("Audio Speech synthesis is not supported on this browser.");
    return;
  }

  if (window.speechSynthesis.speaking) {
    window.speechSynthesis.cancel();
    if (btnSpeak) {
      btnSpeak.classList.remove("speaking");
      btnSpeak.querySelector("span").textContent = "Listen to Script";
    }
    return;
  }

  const text = scriptEl.textContent.trim();
  speechUtterance = new SpeechSynthesisUtterance(text);
  speechUtterance.rate = 1.0;
  speechUtterance.pitch = 1.0;
  speechUtterance.lang = 'en-US';

  speechUtterance.onstart = () => {
    if (btnSpeak) {
      btnSpeak.classList.add("speaking");
      btnSpeak.querySelector("span").textContent = "Stop Audio";
    }
  };

  speechUtterance.onend = () => {
    if (btnSpeak) {
      btnSpeak.classList.remove("speaking");
      btnSpeak.querySelector("span").textContent = "Listen to Script";
    }
  };

  window.speechSynthesis.speak(speechUtterance);
}

function copyCyberFraudDossier() {
  if (!activeCase) return;
  const c = activeCase;
  const trig = c.alert.trigger_transaction;
  const rec = c.policy_result ? c.policy_result.recommended_action : "BLOCK_ACCOUNT";

  const dossierText = `===============================================================
NATIONAL CYBER CRIME REPORTING PORTAL (1930 / NCRP) INCIDENT DOSSIER
BANK OFD DIGITAL PAYMENT FRAUD CONTAINMENT SUMMARY
===============================================================
Case ID: ${c.case_id}
Alert Type: ${c.alert.alert_type} (${c.alert.severity})
Customer Name: ${c.customer_profile.full_name}
Account Number: ${c.customer_profile.account_number}
Registered Mobile: ${c.customer_profile.phone}
Home Circle: ${c.customer_profile.registered_city}, ${c.customer_profile.registered_state}

TRANSACTION UNDER DISPUTE:
- Transaction ID: ${trig.transaction_id}
- Amount: ${formatINR(trig.amount)} INR
- Payment Channel: ${trig.channel}
- Destination Beneficiary / Merchant: ${trig.merchant_name}
- Timestamp: ${trig.timestamp}

SUSPICIOUS TELEMETRY & FRAUD INDICATORS:
- Origin IP: ${c.alert.device_telemetry.ip_address} (${c.alert.device_telemetry.city}, ${c.alert.device_telemetry.country})
- Device Environment: ${c.alert.device_telemetry.device_os} / ${c.alert.device_telemetry.browser}
- Proxy / VPN Active: ${c.alert.device_telemetry.is_vpn_or_proxy ? 'YES' : 'NO'}
- Biometric Liveness Confidence: ${((c.alert.device_telemetry.biometric_confidence_score || 0) * 100).toFixed(0)}%

RECOMMENDED ACTION PER RBI SOP:
- Primary Remediation: ${rec}
- Applicable Policy Code: ${c.policy_result ? c.policy_result.sop_reference : 'SOP-SEC-802'}
- Headline: ${c.consolidated_summary ? c.consolidated_summary.headline : ''}
===============================================================`;

  navigator.clipboard.writeText(dossierText).then(() => {
    const btn = document.getElementById("btn-copy-dossier");
    if (btn) {
      const origText = btn.querySelector("span").textContent;
      btn.querySelector("span").textContent = "✓ Copied 1930!";
      setTimeout(() => {
        btn.querySelector("span").textContent = origText;
      }, 2500);
    }
  }).catch((err) => {
    console.error("Clipboard copy error:", err);
  });
}


