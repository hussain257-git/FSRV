import asyncio
import logging
import time
from typing import Dict, Any, List, Tuple
from app.models.alert import FraudAlert, CustomerProfile
from app.models.agent_results import (
    CustomerProfilingResult,
    CaseHistoryResult,
    NotesSummarizationResult,
    PolicyDecisionResult
)
from app.models.case import ConsolidatedSummary, AuditLogEntry
from app.agents.profiling_agent import CustomerProfilingAgent
from app.agents.history_agent import CaseHistoryAgent
from app.agents.notes_agent import NotesSummarizationAgent
from app.agents.policy_agent import PolicyDecisionAgent

logger = logging.getLogger("agent.investigation")

class InvestigationAgent:
    """
    Central Coordinator in Architecture Diagram:
    Receives trigger from Case Orchestrator Agent (Step 3).
    Coordinates:
      - Step 4: Cust Profiling Agent (ECPR, OPS, DPMS, DCBS, TMS, etc.)
      - Step 5: Case History Agent (CRA, Orig, TFS)
      - Step 6: Notes Summarization Agent (PCFD, Pindrop call logs)
      - Step 7: Policy Decision Agent (OFD, ATO, EEDE, FPF, DTFR, RCDV)
    Produces consolidated intelligence, next-step plan, and returns to Orchestrator (Step 8).
    """
    def __init__(self):
        self.name = "Investigation Agent"
        self.profiling_agent = CustomerProfilingAgent()
        self.history_agent = CaseHistoryAgent()
        self.notes_agent = NotesSummarizationAgent()
        self.policy_agent = PolicyDecisionAgent()

    async def conduct_investigation(
        self,
        alert: FraudAlert,
        customer: CustomerProfile,
        raw_history: List[Dict[str, Any]] = None,
        raw_notes: List[Dict[str, Any]] = None
    ) -> Tuple[
        CustomerProfilingResult,
        CaseHistoryResult,
        NotesSummarizationResult,
        PolicyDecisionResult,
        ConsolidatedSummary,
        List[AuditLogEntry]
    ]:
        start_time = time.perf_counter()
        audit_entries: List[AuditLogEntry] = []

        def log_event(actor: str, action: str, details: str):
            from datetime import datetime, timezone
            audit_entries.append(AuditLogEntry(
                timestamp=datetime.now(timezone.utc).isoformat(),
                actor=actor,
                action=action,
                details=details
            ))

        log_event(self.name, "INVESTIGATION_STARTED", f"Dispatched parallel data gathering for alert {alert.alert_id}")

        # Step 4, 5, 6: Parallel data gathering across microservices
        profiling_task = asyncio.create_task(
            self.profiling_agent.profile_customer(customer, alert)
        )
        history_task = asyncio.create_task(
            self.history_agent.fetch_history(customer, alert, raw_history)
        )
        notes_task = asyncio.create_task(
            self.notes_agent.summarize_notes(customer, alert, raw_notes)
        )

        profiling_result, history_result, notes_result = await asyncio.gather(
            profiling_task, history_task, notes_task
        )

        log_event(
            self.profiling_agent.name, 
            "PROFILING_COMPLETED", 
            f"Evaluated telemetry. Distance: {profiling_result.geolocation_distance_miles:.0f} mi. Spend Dev: {profiling_result.spend_deviation_factor}x."
        )
        log_event(
            self.history_agent.name, 
            "HISTORY_FETCHED", 
            f"Consulted CRA/TFS. {history_result.total_prior_cases} prior cases ({history_result.confirmed_fraud_count} confirmed fraud)."
        )
        log_event(
            self.notes_agent.name, 
            "NOTES_SUMMARIZED", 
            f"Extracted {len(notes_result.bullet_points)} key bullet points. Travel notice detected: {bool(notes_result.detected_travel_notice)}."
        )

        # Step 7: Policy Decision Agent evaluates SOPs and produces Red/Green flags
        policy_result = await self.policy_agent.evaluate_policy(
            alert=alert,
            profiling=profiling_result,
            history=history_result,
            notes=notes_result
        )

        log_event(
            self.policy_agent.name, 
            "POLICY_EVALUATED", 
            f"Evaluated SOP {policy_result.policy_pack}. Risk Score: {policy_result.risk_score}/100 ({policy_result.risk_level}). Red Flags: {len(policy_result.red_flags)}, Green Flags: {len(policy_result.green_flags)}."
        )

        # Step 8: Assemble Consolidated Actionable Summary
        duration_ms = (time.perf_counter() - start_time) * 1000
        summary = self._generate_consolidated_summary(
            alert, customer, profiling_result, history_result, notes_result, policy_result, duration_ms
        )

        log_event(
            self.name, 
            "INVESTIGATION_CONCLUDED", 
            f"Consolidated analysis and next steps compiled in {duration_ms:.1f}ms."
        )

        return (
            profiling_result,
            history_result,
            notes_result,
            policy_result,
            summary,
            audit_entries
        )

    def _generate_consolidated_summary(
        self,
        alert: FraudAlert,
        customer: CustomerProfile,
        profiling: CustomerProfilingResult,
        history: CaseHistoryResult,
        notes: NotesSummarizationResult,
        policy: PolicyDecisionResult,
        duration_ms: float
    ) -> ConsolidatedSummary:
        # Confidence calculation based on data completeness
        confidence = 0.96 if profiling.linked_systems_consulted and history.systems_consulted else 0.85

        # Format Headline
        headline = (
            f"[{policy.risk_level} RISK - SCORE {policy.risk_score}/100] "
            f"{alert.alert_type} detected on account {customer.account_number} ({customer.full_name}). "
            f"Recommended Action: {policy.recommended_action_title}."
        )

        # Key findings summary
        findings = [
            f"Transaction of ₹{alert.trigger_transaction.amount:,.2f} via {alert.trigger_transaction.channel} to {alert.trigger_transaction.merchant_name} (Spend Deviation: {profiling.spend_deviation_factor:.1f}x baseline profile).",
            f"Session Telemetry: {alert.device_telemetry.city}, {alert.device_telemetry.country} ({profiling.geolocation_distance_miles:,.0f} km from registered residence in {customer.registered_city}, {customer.registered_state}).",
            f"Triggered {len(policy.red_flags)} Red Flag(s) and {len(policy.green_flags)} Green Flag(s) under SOP {policy.sop_reference}.",
            f"Historical Relationship: {history.account_relationship_summary}",
            f"Notes Synthesis: {notes.bullet_points[0] if notes.bullet_points else 'No prior negative notes on file.'}"
        ]

        # 1. Case Beginning (Genesis & Baseline)
        case_beginning = [
            f"Customer Profile: {customer.full_name} ({customer.account_type}, tenure {customer.account_tenure_months} mos) registered in {customer.registered_city}, {customer.registered_state}.",
            f"Account Baseline: Normal turnover ₹{customer.avg_monthly_volume_usd:,.2f}/mo with {len(customer.active_cards)} active banking instrument(s).",
            f"Alert Inception: Rule '{alert.rule_name}' triggered at {alert.timestamp[:19].replace('T', ' ')} UTC.",
            f"Transaction Under Review: ₹{alert.trigger_transaction.amount:,.2f} via {alert.trigger_transaction.channel} to {alert.trigger_transaction.merchant_name}."
        ]

        # 2. Key Events Happened (Forensic Attack Timeline)
        key_events = []
        if notes.bullet_points:
            for bp in notes.bullet_points:
                key_events.append(f"Forensic Intelligence: {bp}")
        key_events.append(
            f"Session Telemetry: Request from {alert.device_telemetry.city}, {alert.device_telemetry.country} (IP: {alert.device_telemetry.ip_address}) — {profiling.geolocation_distance_miles:,.0f} km displacement."
        )
        key_events.append(
            f"Device Integrity: {alert.device_telemetry.device_os} / {alert.device_telemetry.browser} (Biometric: {alert.device_telemetry.biometric_confidence_score:.2f}, Proxy/VPN: {alert.device_telemetry.is_vpn_or_proxy})."
        )
        if profiling.spend_deviation_factor > 1.2:
            key_events.append(
                f"Velocity Spike: Spend velocity breach of {profiling.spend_deviation_factor:.1f}x normal baseline threshold."
            )

        # Suggested investigator call script with natural, conversational English
        curr_symbol = "₹"
        if policy.risk_level in ["CRITICAL", "HIGH"]:
            script = (
                f"Analyst Phone Script (Customer Outreach): 'Good day {customer.full_name}, this is the Fraud Prevention & Cyber Security Desk calling from your bank. "
                f"We noticed an unusual {alert.trigger_transaction.channel} payment attempt of {curr_symbol}{alert.trigger_transaction.amount:,.2f} to {alert.trigger_transaction.merchant_name} "
                f"originating from {alert.device_telemetry.city}, {alert.device_telemetry.country}. "
                f"As a safety precaution to safeguard your account, we have placed a temporary protective lock on this transaction. "
                f"Could you please confirm if you or someone authorized by you initiated this payment?'"
            )
        else:
            script = (
                f"Routine Courtesy Verification: 'Good day {customer.full_name}, this is your bank's fraud desk confirming your "
                f"recent payment of {curr_symbol}{alert.trigger_transaction.amount:,.2f} at {alert.trigger_transaction.merchant_name} in {alert.device_telemetry.city}. "
                f"Your biometric verification and travel details have been verified successfully. No action is needed on your part. Thank you for banking with us.'"
            )

        # 3. Actionable Next Steps Plan
        next_steps = [
            f"[IMMEDIATE ACTION] Execute {policy.recommended_action} ({policy.action_urgency}) under SOP {policy.sop_reference}.",
            f"[CYBER PORTAL SYNC] Trigger 1-Click submission to 1930 / NCRP Portal for inter-bank beneficiary lien hold.",
            f"[CUSTOMER OUTREACH] Contact {customer.full_name} via verified telephony script (English / Hindi / Marathi).",
            f"[REGULATORY AUDIT] Document tamper-evident SHA-256 audit entry and RBI zero-liability compliance dispute reference."
        ]

        return ConsolidatedSummary(
            headline=headline,
            risk_assessment=policy.decision_rationale,
            confidence_score=confidence,
            key_findings=findings,
            case_beginning=case_beginning,
            key_events_happened=key_events,
            suggested_investigator_script=script,
            next_step_plan=next_steps
        )
