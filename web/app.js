// PREVENT UI — Bank Fraud Investigation Assist Client Logic
let currentCases = [];
let activeCase = null;
let currentFilter = "ALL";
let pendingActionType = null;
let currentScriptLang = "en";

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

  // Theme Toggle (Dark / Light Mode)
  const btnTheme = document.getElementById("btn-theme-toggle");
  const themeIcon = document.getElementById("theme-toggle-icon");
  const savedTheme = localStorage.getItem("prevent_theme") || "dark";
  if (savedTheme === "light") {
    document.body.setAttribute("data-theme", "light");
    if (themeIcon) themeIcon.textContent = "☀️";
  }
  if (btnTheme) {
    btnTheme.addEventListener("click", () => {
      const isLight = document.body.getAttribute("data-theme") === "light";
      if (isLight) {
        document.body.removeAttribute("data-theme");
        localStorage.setItem("prevent_theme", "dark");
        if (themeIcon) themeIcon.textContent = "🌙";
      } else {
        document.body.setAttribute("data-theme", "light");
        localStorage.setItem("prevent_theme", "light");
        if (themeIcon) themeIcon.textContent = "☀️";
      }
    });
  }

  // Multi-Lingual Script Switcher Chips
  const langChips = document.querySelectorAll(".lang-chip");
  langChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      langChips.forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      currentScriptLang = chip.getAttribute("data-lang");
      if (activeCase) {
        updateCustomerScript(activeCase);
      }
    });
  });

  // 1930 NCRP Modal Handlers
  setupNcrpModal();

  // Export Case Dossier Handlers
  setupDossierExport();

  // What-If Sandbox Handlers
  setupWhatIfListeners();

  // Mule Hierarchy Freeze Button
  const btnMuleFreeze = document.getElementById("btn-mule-freeze");
  if (btnMuleFreeze) {
    btnMuleFreeze.addEventListener("click", () => {
      alert("NPCI Central Switch: Direct Lien Hold broadcasted to all downstream beneficiary accounts.");
      btnMuleFreeze.textContent = "✓ Beneficiary Tree Frozen";
      btnMuleFreeze.disabled = true;
    });
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
  updateSpeedometer(riskScore);

  // Metadata Strip (Indian Banking context)
  document.getElementById("meta-customer-name").textContent = c.customer_profile.full_name;
  document.getElementById("meta-account-num").textContent = c.customer_profile.account_number;
  document.getElementById("meta-tx-amount").textContent = `${formatINR(c.alert.trigger_transaction.amount)} INR`;
  document.getElementById("meta-channel").textContent = `${c.alert.trigger_transaction.channel} (${c.alert.trigger_transaction.merchant_name})`;
  document.getElementById("meta-location").textContent = `${c.alert.device_telemetry.city}, ${c.alert.device_telemetry.country} ${c.alert.device_telemetry.is_vpn_or_proxy ? '(Proxy/VPN)' : ''}`;
  document.getElementById("meta-home").textContent = `${c.customer_profile.registered_city}, ${c.customer_profile.registered_state}`;

  // Render Live Precursor Transaction Sequence & Geo Route
  renderTransactionStream(c);
  renderGeoThreatMap(c);

  // Consolidated Summary (3-Part Operational Narrative)
  if (c.consolidated_summary) {
    document.getElementById("summary-headline").textContent = c.consolidated_summary.headline;
    document.getElementById("summary-assessment").textContent = c.consolidated_summary.risk_assessment;
    document.getElementById("summary-confidence").textContent = `Confidence: ${(c.consolidated_summary.confidence_score * 100).toFixed(0)}%`;

    // 1. Case Beginning (Genesis & Baseline)
    const beginningList = document.getElementById("summary-beginning-list");
    if (beginningList) {
      const beginningItems = c.consolidated_summary.case_beginning || c.consolidated_summary.key_findings.slice(0, 3);
      beginningList.innerHTML = beginningItems.map((f) => `<li>${f}</li>`).join("");
    }

    // 2. Key Events Happened (Forensic Attack Timeline)
    const eventsList = document.getElementById("summary-events-list");
    if (eventsList) {
      const eventItems = c.consolidated_summary.key_events_happened || c.consolidated_summary.key_findings.slice(2);
      eventsList.innerHTML = eventItems.map((e) => `<li>${e}</li>`).join("");
    }

    // Legacy findings list for backward compatibility
    const findingsList = document.getElementById("summary-findings-list");
    if (findingsList) {
      findingsList.innerHTML = c.consolidated_summary.key_findings.map((f) => `<li>${f}</li>`).join("");
    }

    // 3. Next Steps Plan (Prescriptive SOP Remediation)
    const stepsList = document.getElementById("summary-steps-list");
    stepsList.innerHTML = c.consolidated_summary.next_step_plan.map((s) => `<li>${s}</li>`).join("");

    document.getElementById("summary-script").textContent = c.consolidated_summary.suggested_investigator_script || "No specific verbal verification script required for this scenario.";
    updateCustomerScript(c);
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
    renderMuleFlowGraph(c);
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
    initWhatIfSandbox(c);
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
        analyst_id: "OFD-LEAD-409",
        analyst_name: "Hussain Basha Shaik",
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
  if (currentScriptLang === 'hi') {
    speechUtterance.lang = 'hi-IN';
  } else if (currentScriptLang === 'mr') {
    speechUtterance.lang = 'mr-IN';
  } else {
    speechUtterance.lang = 'en-IN';
  }

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

// ==========================================================================
// 1. SPEEDOMETER GAUGE ANIMATION
// ==========================================================================
function updateSpeedometer(score) {
  const meter = document.getElementById("gauge-meter-path");
  if (!meter) return;
  const maxDash = 228;
  const validScore = Math.max(0, Math.min(100, Number(score) || 0));
  const offset = maxDash - (maxDash * (validScore / 100));
  meter.style.strokeDashoffset = offset;
}

// ==========================================================================
// 2. INTERACTIVE GEOLOCATION THREAT VECTOR MAP & VELOCITY RADAR
// ==========================================================================
function renderGeoThreatMap(c) {
  const svg = document.getElementById("geo-radar-svg");
  if (!svg) return;

  const cityCoords = {
    "Mumbai": { x: 530, y: 125, state: "MH" },
    "Delhi": { x: 520, y: 90, state: "DL" },
    "Bengaluru": { x: 535, y: 155, state: "KA" },
    "Chennai": { x: 545, y: 155, state: "TN" },
    "Kolkata": { x: 575, y: 115, state: "WB" },
    "Pune": { x: 532, y: 130, state: "MH" },
    "Nagpur": { x: 542, y: 120, state: "MH" },
    "Lagos": { x: 260, y: 135, country: "NG" },
    "Moscow": { x: 440, y: 55, country: "RU" },
    "Bucharest": { x: 410, y: 80, country: "RO" },
    "Purnia": { x: 568, y: 108, country: "IN" },
    "Noida": { x: 522, y: 92, country: "IN" }
  };

  const homeCity = c.customer_profile.registered_city || "Mumbai";
  const originCity = c.alert.device_telemetry.city || "Lagos";

  const homePos = cityCoords[homeCity] || { x: 530, y: 125 };
  const originPos = cityCoords[originCity] || { x: 260, y: 135 };

  const distKm = c.profiling_result ? Math.round(c.profiling_result.geolocation_distance_miles * 1.609) : 5820;
  const isVpn = c.alert.device_telemetry.is_vpn_or_proxy;
  const isFP = (c.policy_result && c.policy_result.risk_level === "LOW");

  // Update pills
  const distPill = document.getElementById("geo-threat-dist-pill");
  const speedPill = document.getElementById("geo-threat-speed-pill");
  const asnPill = document.getElementById("geo-threat-asn-pill");

  if (distPill) distPill.textContent = `📍 ${distKm.toLocaleString()} km trajectory`;
  if (speedPill) {
    if (isFP) {
      speedPill.textContent = `⚡ 45 km/h (Normal Domestic Velocity)`;
      speedPill.className = "geo-stat-pill";
    } else if (distKm > 1000) {
      speedPill.textContent = `⚡ 87,300 km/h (Impossible Velocity Anomaly)`;
      speedPill.className = "geo-stat-pill alert";
    } else {
      speedPill.textContent = `⚡ High Velocity Geo Jump`;
      speedPill.className = "geo-stat-pill alert";
    }
  }
  if (asnPill) {
    asnPill.textContent = isVpn ? `🌐 AS37148 / Tor-VPN Gateway` : `🌐 Cellular ASN / CSP Node`;
  }

  // Update Legend text
  const legHome = document.getElementById("legend-home-text");
  const legOrigin = document.getElementById("legend-origin-text");
  const legChannel = document.getElementById("legend-channel-text");
  if (legHome) legHome.textContent = `${homeCity}, ${c.customer_profile.registered_state}`;
  if (legOrigin) legOrigin.textContent = `${originCity}, ${c.alert.device_telemetry.country} ${isVpn ? '(VPN/Proxy)' : ''}`;
  if (legChannel) legChannel.textContent = `${c.alert.trigger_transaction.channel} / ${c.alert.trigger_transaction.merchant_name}`;

  // Calculate curved trajectory
  const midX = (homePos.x + originPos.x) / 2;
  const midY = Math.min(homePos.y, originPos.y) - 45;
  const pathD = `M ${homePos.x} ${homePos.y} Q ${midX} ${midY} ${originPos.x} ${originPos.y}`;

  svg.innerHTML = `
    <defs>
      <linearGradient id="trajGradient" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#3b82f6" />
        <stop offset="100%" stop-color="${isFP ? '#10b981' : '#ef4444'}" />
      </linearGradient>
      <filter id="nodeGlow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="3" result="blur" />
        <feMerge>
          <feMergeNode in="blur" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
    </defs>

    <!-- Radar Grid Background -->
    <line x1="0" y1="55" x2="820" y2="55" stroke="rgba(255,255,255,0.04)" stroke-dasharray="4 4" />
    <line x1="0" y1="110" x2="820" y2="110" stroke="rgba(255,255,255,0.06)" />
    <line x1="0" y1="165" x2="820" y2="165" stroke="rgba(255,255,255,0.04)" stroke-dasharray="4 4" />
    <line x1="205" y1="0" x2="205" y2="220" stroke="rgba(255,255,255,0.04)" stroke-dasharray="4 4" />
    <line x1="410" y1="0" x2="410" y2="220" stroke="rgba(255,255,255,0.06)" />
    <line x1="615" y1="0" x2="615" y2="220" stroke="rgba(255,255,255,0.04)" stroke-dasharray="4 4" />

    <!-- Continents Silhouettes -->
    <path d="M 230 110 Q 240 140 280 160 Q 310 180 340 140 Q 350 100 300 90 Z" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.08)" stroke-width="1" />
    <path d="M 390 50 Q 450 40 480 65 Q 460 90 420 85 Z" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.08)" stroke-width="1" />
    <path d="M 500 80 Q 560 70 600 95 Q 580 150 530 170 Q 500 130 500 80 Z" fill="rgba(59, 130, 246, 0.05)" stroke="rgba(59, 130, 246, 0.15)" stroke-width="1" />

    <!-- Concentric Range Circles from Home -->
    <circle cx="${homePos.x}" cy="${homePos.y}" r="35" fill="none" stroke="rgba(59, 130, 246, 0.2)" stroke-dasharray="2 4" />
    <circle cx="${homePos.x}" cy="${homePos.y}" r="70" fill="none" stroke="rgba(59, 130, 246, 0.12)" stroke-dasharray="3 5" />
    <circle cx="${homePos.x}" cy="${homePos.y}" r="110" fill="none" stroke="rgba(59, 130, 246, 0.08)" stroke-dasharray="4 6" />

    <!-- Trajectory Path with Arc Dash Animation -->
    <path d="${pathD}" fill="none" stroke="url(#trajGradient)" stroke-width="2.5" stroke-dasharray="6 4" filter="url(#nodeGlow)">
      <animate attributeName="stroke-dashoffset" from="100" to="0" dur="2s" repeatCount="indefinite" />
    </path>

    <!-- Traveling Photon Packet -->
    <circle r="4" fill="#ffffff" filter="url(#nodeGlow)">
      <animateMotion path="${pathD}" dur="2.2s" repeatCount="indefinite" />
    </circle>

    <!-- Origin Node & Radar Pulse Wave -->
    <circle cx="${originPos.x}" cy="${originPos.y}" r="16" fill="none" stroke="${isFP ? '#10b981' : '#ef4444'}" opacity="0.6">
      <animate attributeName="r" from="6" to="26" dur="1.8s" repeatCount="indefinite" />
      <animate attributeName="opacity" from="0.8" to="0" dur="1.8s" repeatCount="indefinite" />
    </circle>
    <circle cx="${originPos.x}" cy="${originPos.y}" r="6" fill="${isFP ? '#10b981' : '#ef4444'}" filter="url(#nodeGlow)" />
    <text x="${originPos.x}" y="${originPos.y - 12}" fill="${isFP ? '#6ee7b7' : '#fca5a5'}" font-size="10" font-weight="700" text-anchor="middle">${originCity}</text>

    <!-- Home Node -->
    <circle cx="${homePos.x}" cy="${homePos.y}" r="6" fill="#3b82f6" filter="url(#nodeGlow)" />
    <circle cx="${homePos.x}" cy="${homePos.y}" r="12" fill="none" stroke="#60a5fa" stroke-width="1.5" opacity="0.6" />
    <text x="${homePos.x}" y="${homePos.y + 18}" fill="#93c5fd" font-size="10" font-weight="700" text-anchor="middle">${homeCity} (Home)</text>
  `;
}

// ==========================================================================
// 3. MULTI-LINGUAL CUSTOMER SCRIPT SYSTEM
// ==========================================================================
const LOCALIZED_SCRIPTS = {
  "CASE-ATO-8921": {
    en: "Good day Rajesh Kumar Sharma, this is Hussain Basha Shaik from your bank's Fraud Prevention Desk. We have temporarily suspended an outbound IMPS transfer of ₹14,50,000 to Binance Global initiated from an IP in Lagos, Nigeria. Did you authorize this transaction or reset your password in the last 24 hours?",
    hi: "नमस्ते राजेश कुमार शर्मा जी, मैं आपके बैंक के धोखाधड़ी नियंत्रण विभाग से बोल रही हूँ। आपके खाते से लागोस (नाइजीरिया) से ₹14,50,000 का आईएमपीएस (IMPS) ट्रांसफर रोकने के लिए हमने खाते को अस्थायी रूप से सुरक्षित किया है। क्या यह लेन-देन आपने किया था अथवा हाल ही में पासवर्ड बदला था?",
    mr: "नमस्कार राजेश कुमार शर्मा जी, मी आपल्या बँकेच्या फसवणूक नियंत्रण विभागातून बोलत आहे. आपल्या खात्यावरून लागोस, नायजेरिया येथून झालेला ₹१४,५०,००० चा आयएमपीएस व्यवहार आम्ही तात्पुरता थांबवला आहे. हा व्यवहार आपण स्वतः केला होता का?"
  },
  "CASE-CNP-4402": {
    en: "Hello Priya Venkataraman, this is the card fraud containment team. We detected 4 rapid digital gift voucher transactions totaling ₹1,85,000 routed through a foreign proxy network. We have restricted your card for security. Can you verify if you made these purchases on Gyft / Amazon Pay?",
    hi: "नमस्ते प्रिया वेंकटरमण जी, बैंक सुरक्षा टीम से संपर्क किया जा रहा है। आपके कार्ड द्वारा विदेशी प्रॉक्सी नेटवर्क से ₹1,85,000 के 4 त्वरित डिजिटल वाउचर खरीदे जा रहे थे। सुरक्षा कारणों से कार्ड ब्लॉक किया गया है। क्या यह खरीदारी आपने की थी?",
    mr: "नमस्कार प्रिया वेंकटरमण जी, बँक कार्ड सुरक्षा विभागाकडून संपर्क करत आहोत. आपल्या कार्डवरून परदेशी प्रॉक्सीद्वारे ₹१,८५,००० चे ४ डिजिटल व्हाउचर्स व्यवहार आढळले आहेत. काय हे व्यवहार आपण स्वतः केले आहेत?"
  },
  "CASE-FP-1093": {
    en: "Good day Dr. Vikram Singhania, this is your Relationship Desk. We are confirming your in-store jewellery purchase of ₹3,50,000 at Tanishq Jewellers, New Delhi. Our biometric facial scan and prior wedding travel note have successfully verified this transaction. No freeze is required.",
    hi: "नमस्ते डॉ. विक्रम सिंघानिया जी, आपके रिलेशनशिप डेस्क से कॉल है। तनिष्क ज्वैलर्स नई दिल्ली में ₹3,50,000 के आभूषण खरीद की पुष्टि हो गई है। आधार फेस बायोमेट्रिक व विवाह यात्रा सूचना के आधार पर यह लेन-देन पूर्णतः सुरक्षित व स्वीकृत है।",
    mr: "नमस्कार डॉ. विक्रम सिंघानिया जी, तनिष्क ज्वेलर्स नवी दिल्ली येथे झालेला ₹३,५०,००० चा खरेदी व्यवहार आपल्या बायोमेट्रिक पडताळणीनुसार यशस्वीरीत्या मंजूर करण्यात आला आहे. खाते पूर्णपणे सुरक्षित आहे."
  },
  "CASE-ML-6718": {
    en: "Attention Investigator: Amit Verma's account (ACT-7718-4401) is acting as an active Level 1 money mule. The incoming UPI credit of ₹9,85,000 was immediately split into 3 outbound transfers via PhonePe, Binance OTC, and Micro-ATM. Initiate immediate 1930 NCRP beneficiary freeze.",
    hi: "जांच अधिकारी ध्यान दें: अमित वर्मा का खाता (ACT-7718-4401) सक्रिय मनी-म्यूल (Mule Account) के रूप में प्रयुक्त हो रहा है। ₹9,85,000 की यूपीआई राशि तुरंत 3 अन्य खातों में बांटी जा रही थी। तत्काल सभी संबद्ध बैंक खातों को 1930 पोर्टल पर फ्रीज करें।",
    mr: "तपासनीस सूचना: अमित वर्मा यांचे खाते मनी-म्यूल (Money Mule) म्हणून वापरले जात आहे. आलेली ₹९,८५,००० ची रक्कम तात्काळ इतर तीन खात्यांत वळवली जात होती. सर्व संबंधित लाभार्थी खाती त्वरित फ्रीझ करण्याचे आदेश आहेत."
  },
  "CASE-UPI-5104": {
    en: "Hello Sunita Deshmukh, this is your bank's cyber safety desk. Our mobile defense telemetry identified an unauthorized screen-sharing tool (AnyDesk) remotely accessing your device during 3 UPI QR debits totaling ₹85,000. Please immediately disconnect your internet and uninstall AnyDesk.",
    hi: "नमस्ते सुनीता देशमुख जी, बैंक साइबर सुरक्षा टीम से कॉल है। आपके फोन पर स्क्रीन-शेयरिंग ऐप (AnyDesk) द्वारा ₹85,000 के अनाधिकृत यूपीआई डेबिट किए जा रहे थे। कृपया तुरंत अपना इंटरनेट बंद करें और एनीडेस्क ऐप को अनइंस्टॉल करें।",
    mr: "नमस्कार सुनिता देशमुख जी, बँक सायबर सुरक्षा कक्षाकडून महत्त्वाची सूचना. आपल्या मोबाईलवर AnyDesk स्क्रीन शेअरिंग ऍपद्वारे ₹८५,००० चे अनधिकृत व्यवहार रोखण्यात आले आहेत. कृपया लगेच इंटरनेट बंद करा व ते ऍप काढून टाका."
  },
  "CASE-SIM-7731": {
    en: "Good day Arvind Swaminathan, our telecom fraud watch identified a duplicate e-SIM issuance in Noida circle just 3 hours before an unauthorized ₹4,80,000 RTGS dispatch. We have blocked your NetBanking credentials to protect your funds.",
    hi: "नमस्ते अरविंद स्वामीनाथन जी, नोएडा सर्कल में आपके नंबर का डुप्लीकेट ई-सिम जारी होने के 3 घंटे बाद ₹4,80,000 का आरटीजीएस (RTGS) ट्रांसफर करने का प्रयास किया गया। आपकी सुरक्षा हेतु नेटबैंकिंग तुरंत ब्लॉक कर दी गई है।",
    mr: "नमस्कार अरविंद स्वामीनाथन जी, आपल्या मोबाईल नंबरचे डुप्लिकेट ई-सिम जारी झाल्यानंतर ₹४,८०,००० चा आरटीजीएस व्यवहार करण्याचा संशयास्पद प्रयत्न झाला आहे. सुरक्षा म्हणून नेटबँकिंग तात्काळ ब्लॉक करण्यात आले आहे."
  },
  "CASE-AEPS-3209": {
    en: "Ramesh Patil, alert: A cloned silicone biometric fingerprint was presented at a rural Micro-ATM CSP kiosk in Bihar attempting an AEPS cash withdrawal of ₹30,000. Your biometric lock has been engaged per UIDAI safety protocol.",
    hi: "रमेश पाटिल जी, सूचना: बिहार के एक ग्रामीण माइक्रो-एटीएम सीएसपी कियोस्क पर नकली सिलिकॉन फिंगरप्रिंट लगाकर ₹30,000 निकालने का प्रयास पकड़ा गया है। यूआईडीएआई (UIDAI) सुरक्षा नियमों के तहत आपका बायोमेट्रिक लॉक कर दिया गया है।",
    mr: "रमेश पाटील जी, महत्त्वाची सूचना: बिहार येथील मायक्रो-एटीएम केंद्रावर बनावट सिलिकॉन अंगठ्याचा वापर करून ₹३०,००० काढण्याचा प्रयत्न रोखण्यात आला आहे. आधार बायोमेट्रिक सुरक्षा तात्काळ लॉक करण्यात आली आहे."
  },
  "CASE-ONL-6610": {
    en: "Good day Ananya Deshpande, this is your bank's fraud monitoring desk. We intercepted a suspicious international online payment of ₹2,75,000 to UK Crypto Exchange attempted over a Tor exit node just minutes after an interaction on a cloned electricity bill payment site. Have you attempted to pay an electricity bill online today?",
    hi: "नमस्ते अनन्या देशपांडे जी, बैंक फ्रॉड मॉनिटरिंग सेल से कॉल है। बिजली बिल भुगतान के नाम पर बनी फर्जी वेबसाइट द्वारा आपके कार्ड क्रेडेंशियल चोरी कर यूके क्रिप्टो एक्सचेंज पर ₹2,75,000 का ऑनलाइन भुगतान करने का प्रयास किया गया। क्या आपने आज बिजली बिल भरा था?",
    mr: "नमस्कार अनन्या देशपांडे जी, बँक सायबर फसवणूक प्रतिबंधक विभागाकडून संपर्क. महावितरण वीज बिल भरण्याच्या बनावट पोर्टलवरून आपले कार्ड तपशील चोरून युके येथील क्रिप्टो एक्सचेंजवर ₹२,७५,००० चा ऑनलाइन व्यवहार रोखण्यात आला आहे. काय आपण आज वीज बिल भरण्याचा प्रयत्न केला होता?"
  }
};

function updateCustomerScript(c) {
  const scriptEl = document.getElementById("summary-script");
  if (!scriptEl) return;

  const scripts = LOCALIZED_SCRIPTS[c.case_id] || {
    en: c.consolidated_summary ? c.consolidated_summary.suggested_investigator_script : "Verification script active.",
    hi: "नमस्ते, बैंक सुरक्षा विभाग से सत्यापन कॉल। क्या यह लेन-देन आपने किया था?",
    mr: "नमस्कार, बँक सुरक्षा विभागाकडून तपासणी कॉल. हा व्यवहार आपण केला होता का?"
  };

  scriptEl.textContent = scripts[currentScriptLang] || scripts.en;
}

// ==========================================================================
// 4. 1-CLICK 1930 / NCRP PORTAL SYNC MODAL
// ==========================================================================
function setupNcrpModal() {
  const btnOpen = document.getElementById("btn-open-ncrp");
  const modal = document.getElementById("ncrp-modal");
  const btnClose = document.getElementById("btn-ncrp-close");
  const btnCancel = document.getElementById("btn-ncrp-cancel");
  const btnSubmit = document.getElementById("btn-ncrp-submit");
  const btnDownloadJson = document.getElementById("btn-ncrp-download-json");
  const txBox = document.getElementById("ncrp-transmitting-box");

  if (!btnOpen || !modal) return;

  btnOpen.addEventListener("click", () => {
    if (!activeCase) return;
    const c = activeCase;
    const trig = c.alert.trigger_transaction;

    const ackField = document.getElementById("ncrp-ack-id");
    if (ackField) ackField.value = `NCRP-MHA-2026-${c.case_id.replace(/[^0-9]/g, '')}`;

    const victimField = document.getElementById("ncrp-victim-name");
    if (victimField) victimField.value = c.customer_profile.full_name;

    const acctField = document.getElementById("ncrp-victim-acct");
    if (acctField) acctField.value = `${c.customer_profile.account_number} (IFSC: SBIN0001824)`;

    const utrField = document.getElementById("ncrp-tx-utr");
    if (utrField) utrField.value = trig.transaction_id;

    const amtField = document.getElementById("ncrp-amount");
    if (amtField) amtField.value = `${formatINR(trig.amount)} INR`;

    const destField = document.getElementById("ncrp-dest-entity");
    if (destField) destField.value = `${trig.merchant_name} (${trig.channel})`;

    const ipField = document.getElementById("ncrp-origin-ip");
    if (ipField) ipField.value = `${c.alert.device_telemetry.ip_address} [${c.alert.device_telemetry.city}, ${c.alert.device_telemetry.country}]`;

    if (txBox) txBox.classList.add("hidden");
    if (btnSubmit) {
      btnSubmit.disabled = false;
      const span = btnSubmit.querySelector("span");
      if (span) span.textContent = "⚡ Submit & Freeze Inter-Bank Network";
    }

    modal.classList.remove("hidden");
  });

  const closeModal = () => modal.classList.add("hidden");
  if (btnClose) btnClose.addEventListener("click", closeModal);
  if (btnCancel) btnCancel.addEventListener("click", closeModal);

  if (btnSubmit) {
    btnSubmit.addEventListener("click", () => {
      if (txBox) {
        txBox.classList.remove("hidden");
        const s1 = document.getElementById("ncrp-step-1");
        const s2 = document.getElementById("ncrp-step-2");
        const s3 = document.getElementById("ncrp-step-3");

        s1.className = "ncrp-step active";
        s2.className = "ncrp-step";
        s3.className = "ncrp-step";

        setTimeout(() => {
          s1.className = "ncrp-step done";
          s2.className = "ncrp-step active";
        }, 500);

        setTimeout(() => {
          s2.className = "ncrp-step done";
          s3.className = "ncrp-step active";
        }, 1000);

        setTimeout(() => {
          s3.className = "ncrp-step done";
          btnSubmit.disabled = true;
          const span = btnSubmit.querySelector("span");
          if (span) span.textContent = "✓ 1930 Lien Hold Dispatched!";
        }, 1500);
      }
    });
  }

  if (btnDownloadJson) {
    btnDownloadJson.addEventListener("click", () => {
      if (!activeCase) return;
      const ackVal = document.getElementById("ncrp-ack-id") ? document.getElementById("ncrp-ack-id").value : "NCRP-2026";
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify({
        ncrp_docket_id: ackVal,
        reporting_officer: "Hussain Basha Shaik (OFD-LEAD-409)",
        case_id: activeCase.case_id,
        victim_name: activeCase.customer_profile.full_name,
        victim_account: activeCase.customer_profile.account_number,
        transaction_utr: activeCase.alert.trigger_transaction.transaction_id,
        disputed_amount_inr: activeCase.alert.trigger_transaction.amount,
        suspect_entity: activeCase.alert.trigger_transaction.merchant_name,
        origin_telemetry: activeCase.alert.device_telemetry,
        rbi_sop_code: activeCase.policy_result ? activeCase.policy_result.sop_reference : "SOP-SEC-802",
        digital_signature_hash: "SHA256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"
      }, null, 2));

      const downloadAnchor = document.createElement("a");
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `NCRP_Complaint_${activeCase.case_id}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    });
  }
}

// ==========================================================================
// 5. EXPORTABLE BRANDED CASE DOSSIER
// ==========================================================================
function setupDossierExport() {
  const btnExport = document.getElementById("btn-export-dossier");
  const modal = document.getElementById("dossier-modal");
  const btnClose = document.getElementById("btn-dossier-close");
  const btnCancel = document.getElementById("btn-dossier-cancel");
  const btnPrint = document.getElementById("btn-dossier-print");
  const printContent = document.getElementById("dossier-print-content");

  if (!btnExport || !modal) return;

  btnExport.addEventListener("click", () => {
    if (!activeCase) return;
    const c = activeCase;
    const trig = c.alert.trigger_transaction;
    const risk = c.policy_result ? c.policy_result.risk_level : "CRITICAL";
    const score = c.policy_result ? c.policy_result.risk_score : 98;
    const recAction = c.policy_result ? c.policy_result.recommended_action : "BLOCK_ACCOUNT";

    printContent.innerHTML = `
      <div class="dossier-watermark">CONFIDENTIAL • OFD CRIME UNIT</div>
      <div class="dossier-header-grid">
        <div class="dossier-bank-title">
          <h2>BHARAT FINANCIAL INTELLIGENCE &amp; OFD DIVISION</h2>
          <p>Cognitive Anti-Fraud Defense Operations • Cyber Forensic Incident Docket</p>
          <p class="font-mono text-xs" style="margin-top:4px;">REF: ${c.case_id} • TIME: ${new Date().toLocaleString('en-IN')}</p>
        </div>
        <div class="dossier-qr-box">
          <svg width="68" height="68" viewBox="0 0 100 100">
            <rect width="100" height="100" fill="#ffffff" />
            <rect x="5" y="5" width="30" height="30" fill="none" stroke="#000" stroke-width="6" />
            <rect x="15" y="15" width="10" height="10" fill="#000" />
            <rect x="65" y="5" width="30" height="30" fill="none" stroke="#000" stroke-width="6" />
            <rect x="75" y="15" width="10" height="10" fill="#000" />
            <rect x="5" y="65" width="30" height="30" fill="none" stroke="#000" stroke-width="6" />
            <rect x="15" y="75" width="10" height="10" fill="#000" />
            <circle cx="50" cy="50" r="5" fill="#000" />
            <rect x="45" y="15" width="6" height="20" fill="#000" />
            <rect x="15" y="45" width="20" height="6" fill="#000" />
            <rect x="60" y="50" width="25" height="6" fill="#000" />
            <rect x="50" y="70" width="30" height="8" fill="#000" />
          </svg>
          <span class="dossier-qr-label">SHA-256 VERIFIED</span>
        </div>
      </div>

      <div class="dossier-section-title">1. Victim &amp; Account Profiling</div>
      <table class="dossier-table">
        <tr>
          <th>Customer Name</th><td>${c.customer_profile.full_name}</td>
          <th>Account Number</th><td class="font-mono">${c.customer_profile.account_number}</td>
        </tr>
        <tr>
          <th>Home Circle</th><td>${c.customer_profile.registered_city}, ${c.customer_profile.registered_state}</td>
          <th>KYC Status</th><td>Verified (Tenure: ${c.customer_profile.tenure_months || 36} mos)</td>
        </tr>
      </table>

      <div class="dossier-section-title">2. Disputed Payment Telemetry (INR)</div>
      <table class="dossier-table">
        <tr>
          <th>Transaction ID</th><td class="font-mono">${trig.transaction_id}</td>
          <th>Disputed Amount</th><td class="font-mono" style="font-weight:700; color:#1e40af;">${formatINR(trig.amount)} INR</td>
        </tr>
        <tr>
          <th>Payment Channel</th><td>${trig.channel} (${trig.merchant_name})</td>
          <th>Ingestion Coordinates</th><td>${c.alert.device_telemetry.city}, ${c.alert.device_telemetry.country} (${c.alert.device_telemetry.ip_address})</td>
        </tr>
        <tr>
          <th>Proxy / VPN Mask</th><td>${c.alert.device_telemetry.is_vpn_or_proxy ? 'DETECTED (High Risk)' : 'NO (Direct Carrier)'}</td>
          <th>Biometric Liveness</th><td>${((c.alert.device_telemetry.biometric_confidence_score || 0) * 100).toFixed(0)}% Match</td>
        </tr>
      </table>

      <div class="dossier-section-title">3. Cognitive Agent Decision &amp; SOP Reference</div>
      <table class="dossier-table">
        <tr>
          <th>Cognitive Risk Score</th><td><strong>${score} / 100 (${risk} RISK)</strong></td>
          <th>Enforced SOP Action</th><td><strong style="color:#b91c1c;">${recAction}</strong></td>
        </tr>
        <tr>
          <th>Policy Citation</th><td colspan="3">${c.policy_result ? c.policy_result.sop_reference : 'SOP-SEC-802: Emergency Account Containment'}</td>
        </tr>
      </table>

      <div class="dossier-section-title">4. Statutory Verification Sign-Off</div>
      <div style="display:flex; justify-content:space-between; margin-top:16px; font-size:11px; color:#475569;">
        <div>
          <p>Investigating Analyst: <strong>Hussain Basha Shaik (OFD-LEAD-409)</strong></p>
          <p>Digital Digest: <code style="font-family:monospace; font-size:10px;">SHA256:7f83b165...9069</code></p>
        </div>
        <div style="text-align:right;">
          <p>Compliance Directive: <strong>RBI Cyber Security Framework (2026)</strong></p>
          <p>Status: <strong>PROCESSED &amp; ARCHIVED</strong></p>
        </div>
      </div>
    `;

    modal.classList.remove("hidden");
  });

  const closeModal = () => modal.classList.add("hidden");
  if (btnClose) btnClose.addEventListener("click", closeModal);
  if (btnCancel) btnCancel.addEventListener("click", closeModal);
  if (btnPrint) {
    btnPrint.addEventListener("click", () => window.print());
  }
}

// ==========================================================================
// 6. "WHAT-IF" COUNTERFACTUAL POLICY SIMULATOR
// ==========================================================================
function setupWhatIfListeners() {
  const tTravel = document.getElementById("whatif-travel");
  const tDevice = document.getElementById("whatif-device");
  const sBio = document.getElementById("whatif-bio-slider");
  const btnReset = document.getElementById("btn-whatif-reset");

  if (tTravel) tTravel.addEventListener("change", recalculateWhatIf);
  if (tDevice) tDevice.addEventListener("change", recalculateWhatIf);
  if (sBio) {
    sBio.addEventListener("input", (e) => {
      const bioVal = document.getElementById("whatif-bio-val");
      if (bioVal) bioVal.textContent = `${e.target.value}%`;
      recalculateWhatIf();
    });
  }

  if (btnReset) {
    btnReset.addEventListener("click", () => {
      if (activeCase) initWhatIfSandbox(activeCase);
    });
  }
}

function initWhatIfSandbox(c) {
  const tTravel = document.getElementById("whatif-travel");
  const tDevice = document.getElementById("whatif-device");
  const sBio = document.getElementById("whatif-bio-slider");
  const valBio = document.getElementById("whatif-bio-val");

  if (!tTravel || !sBio) return;

  const hasTravel = (c.policy_result && c.policy_result.green_flags.some((g) => g.rule_id.includes("TRAVEL") || g.rule_id.includes("NOTIF")));
  const deviceTrust = c.profiling_result ? c.profiling_result.device_trust_score > 0.6 : false;
  const bioScore = c.alert.device_telemetry.biometric_confidence_score ? Math.round(c.alert.device_telemetry.biometric_confidence_score * 100) : 15;

  tTravel.checked = Boolean(hasTravel);
  tDevice.checked = Boolean(deviceTrust);
  sBio.value = bioScore;
  if (valBio) valBio.textContent = `${bioScore}%`;

  recalculateWhatIf();
}

function recalculateWhatIf() {
  if (!activeCase) return;
  const tTravel = document.getElementById("whatif-travel");
  const tDevice = document.getElementById("whatif-device");
  const sBio = document.getElementById("whatif-bio-slider");

  const hasTravel = tTravel ? tTravel.checked : false;
  const hasKnownDevice = tDevice ? tDevice.checked : false;
  const bioVal = sBio ? parseInt(sBio.value, 10) : 15;

  let simScore = 95;
  if (hasTravel) simScore -= 35;
  if (hasKnownDevice) simScore -= 25;
  if (bioVal >= 70) simScore -= 45;
  else if (bioVal >= 40) simScore -= 20;

  simScore = Math.max(8, Math.min(99, simScore));

  const actionEl = document.getElementById("whatif-sim-action");
  const scoreEl = document.getElementById("whatif-sim-score");
  const rationaleEl = document.getElementById("whatif-sim-rationale");

  if (scoreEl) scoreEl.textContent = `Simulated Risk: ${simScore}/100`;

  if (simScore <= 30) {
    if (actionEl) {
      actionEl.textContent = "DISMISS_FALSE_POSITIVE";
      actionEl.className = "whatif-action-pill success";
    }
    if (rationaleEl) {
      rationaleEl.textContent = "Hypothetical Outcome: Confirmed travel notification combined with verified biometric match neutralizes the anomalous geo-hop. Transaction qualifies for automated clearance under SOP-EXEMP-105.";
    }
  } else if (simScore <= 65) {
    if (actionEl) {
      actionEl.textContent = "CONTACT_CUSTOMER";
      actionEl.className = "whatif-action-pill warning";
    }
    if (rationaleEl) {
      rationaleEl.textContent = "Hypothetical Outcome: Partial identity verification present, but intermediate biometric confidence requires customer verbal verification callback before clearing wire.";
    }
  } else {
    if (actionEl) {
      actionEl.textContent = "BLOCK_ACCOUNT";
      actionEl.className = "whatif-action-pill danger";
    }
    if (rationaleEl) {
      rationaleEl.textContent = "Hypothetical Outcome: Absence of travel notice combined with unverified device telemetry mandates immediate credential freeze per SOP-SEC-802.";
    }
  }
}

// ==========================================================================
// 7. MULE FUND FLOW NETWORK TOPOLOGY GRAPH
// ==========================================================================
function renderMuleFlowGraph(c) {
  const svg = document.getElementById("mule-flow-svg");
  const panel = document.getElementById("mule-network-panel");
  if (!svg || !panel) return;

  const isMule = (c.alert.alert_type === "MULE_NETWORK" || c.case_id.includes("ML"));
  const muleBadge = document.getElementById("mule-badge");

  if (isMule) {
    if (muleBadge) muleBadge.textContent = "Multi-Hop Layering Detected";
  } else {
    if (muleBadge) muleBadge.textContent = "Standard Single-Hop Settlement";
  }

  svg.innerHTML = `
    <defs>
      <linearGradient id="linkGradIn" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#ef4444" />
        <stop offset="100%" stop-color="#f59e0b" />
      </linearGradient>
      <linearGradient id="linkGradOut" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#f59e0b" />
        <stop offset="100%" stop-color="#8b5cf6" />
      </linearGradient>
      <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation="2" result="b" />
        <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
    </defs>

    <!-- Inbound Links -->
    <path d="M 170 45 Q 260 70 320 105" fill="none" stroke="url(#linkGradIn)" stroke-width="2" stroke-dasharray="4 3">
      <animate attributeName="stroke-dashoffset" from="20" to="0" dur="1.2s" repeatCount="indefinite" />
    </path>
    <path d="M 170 105 L 320 105" fill="none" stroke="url(#linkGradIn)" stroke-width="2.5" stroke-dasharray="4 3">
      <animate attributeName="stroke-dashoffset" from="20" to="0" dur="1s" repeatCount="indefinite" />
    </path>
    <path d="M 170 165 Q 260 140 320 105" fill="none" stroke="url(#linkGradIn)" stroke-width="2" stroke-dasharray="4 3">
      <animate attributeName="stroke-dashoffset" from="20" to="0" dur="1.4s" repeatCount="indefinite" />
    </path>

    <!-- Outbound Links -->
    <path d="M 460 105 Q 520 70 590 45" fill="none" stroke="url(#linkGradOut)" stroke-width="2" stroke-dasharray="4 3">
      <animate attributeName="stroke-dashoffset" from="0" to="20" dur="1.2s" repeatCount="indefinite" />
    </path>
    <path d="M 460 105 L 590 105" fill="none" stroke="url(#linkGradOut)" stroke-width="2.5" stroke-dasharray="4 3">
      <animate attributeName="stroke-dashoffset" from="0" to="20" dur="1s" repeatCount="indefinite" />
    </path>
    <path d="M 460 105 Q 520 140 590 165" fill="none" stroke="url(#linkGradOut)" stroke-width="2" stroke-dasharray="4 3">
      <animate attributeName="stroke-dashoffset" from="0" to="20" dur="1.4s" repeatCount="indefinite" />
    </path>

    <!-- Left Nodes: Victim Sources -->
    <g transform="translate(30, 25)">
      <rect width="140" height="38" rx="6" fill="#1e293b" stroke="#ef4444" stroke-width="1.2" />
      <text x="10" y="16" fill="#fca5a5" font-size="10" font-weight="700">Source Victim 1</text>
      <text x="10" y="30" fill="#f8fafc" font-size="11" font-family="monospace">₹3,50,000 (UPI)</text>
    </g>
    <g transform="translate(30, 85)">
      <rect width="140" height="38" rx="6" fill="#1e293b" stroke="#ef4444" stroke-width="1.2" />
      <text x="10" y="16" fill="#fca5a5" font-size="10" font-weight="700">Source Victim 2</text>
      <text x="10" y="30" fill="#f8fafc" font-size="11" font-family="monospace">₹4,20,000 (IMPS)</text>
    </g>
    <g transform="translate(30, 145)">
      <rect width="140" height="38" rx="6" fill="#1e293b" stroke="#ef4444" stroke-width="1.2" />
      <text x="10" y="16" fill="#fca5a5" font-size="10" font-weight="700">Source Victim 3</text>
      <text x="10" y="30" fill="#f8fafc" font-size="11" font-family="monospace">₹2,15,000 (UPI)</text>
    </g>

    <!-- Center Node: Layer 1 Mule Account -->
    <g transform="translate(320, 75)">
      <rect width="140" height="60" rx="8" fill="#1e293b" stroke="#f59e0b" stroke-width="2" filter="url(#glow)" />
      <text x="70" y="20" fill="#fde047" font-size="11" font-weight="800" text-anchor="middle">LAYER 1 MULE HUB</text>
      <text x="70" y="36" fill="#f8fafc" font-size="10" text-anchor="middle">${c.customer_profile.full_name}</text>
      <text x="70" y="50" fill="#94a3b8" font-size="9" font-family="monospace" text-anchor="middle">ACT-${c.customer_profile.account_number.slice(-4)}</text>
    </g>

    <!-- Right Nodes: Layer 2 Dispersion -->
    <g transform="translate(590, 25)">
      <rect width="145" height="38" rx="6" fill="#1e293b" stroke="#8b5cf6" stroke-width="1.2" />
      <text x="10" y="16" fill="#c4b5fd" font-size="10" font-weight="700">Outflow: PhonePe VPA</text>
      <text x="10" y="30" fill="#f8fafc" font-size="11" font-family="monospace">₹3,00,000 (Dispersed)</text>
    </g>
    <g transform="translate(590, 85)">
      <rect width="145" height="38" rx="6" fill="#1e293b" stroke="#8b5cf6" stroke-width="1.2" />
      <text x="10" y="16" fill="#c4b5fd" font-size="10" font-weight="700">Outflow: Binance P2P</text>
      <text x="10" y="30" fill="#f8fafc" font-size="11" font-family="monospace">₹4,50,000 (Crypto USDT)</text>
    </g>
    <g transform="translate(590, 145)">
      <rect width="145" height="38" rx="6" fill="#1e293b" stroke="#8b5cf6" stroke-width="1.2" />
      <text x="10" y="16" fill="#c4b5fd" font-size="10" font-weight="700">Outflow: Micro-ATM CSP</text>
      <text x="10" y="30" fill="#f8fafc" font-size="11" font-family="monospace">₹2,35,000 (Cash-Out)</text>
    </g>
  `;
}


