import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

from app.models.agent_results import (
    PolicyDecisionResult,
    PolicyFlag,
    FlagSeverity,
    FlagType,
    CustomerProfilingResult,
    CaseHistoryResult,
    NotesSummarizationResult
)
from app.models.alert import FraudAlert

class PolicyRuleEngine:
    def __init__(self, rules_file_path: Path = None):
        if rules_file_path is None:
            rules_file_path = Path(__file__).resolve().parent / "rules.json"
        
        with open(rules_file_path, "r", encoding="utf-8") as f:
            self.policy_data = json.load(f)
        
        self.policy_name = self.policy_data.get("policy_name", "OFD_GLOBAL_SOP_v2.4")
        self.rules = self.policy_data.get("rules", [])

    def evaluate(
        self,
        alert: FraudAlert,
        profiling: CustomerProfilingResult,
        history: CaseHistoryResult,
        notes: NotesSummarizationResult
    ) -> PolicyDecisionResult:
        # Build evaluation facts context
        facts = {
            "is_foreign_ip": profiling.is_foreign_ip,
            "is_new_device": alert.device_telemetry.is_new_device,
            "spend_deviation_factor": profiling.spend_deviation_factor,
            "is_vpn_detected": profiling.is_vpn_detected,
            "device_trust_score": profiling.device_trust_score,
            "tenure_months": profiling.tenure_months,
            "velocity_24h_count": profiling.velocity_24h_count,
            "velocity_24h_amount_usd": profiling.velocity_24h_amount_usd,
            "channel": alert.trigger_transaction.channel,
            "two_factor_authenticated": alert.trigger_transaction.two_factor_authenticated,
            "auth_method": alert.trigger_transaction.auth_method or "NONE",
            "biometric_confidence": alert.device_telemetry.biometric_confidence_score or 0.0,
            "confirmed_fraud_count": history.confirmed_fraud_count,
            "false_positive_count": history.false_positive_count,
            "has_matching_travel_notice": bool(notes.detected_travel_notice),
            "has_recent_password_reset": any("password" in s.lower() or "credential" in s.lower() for s in notes.recent_security_events),
            "has_recent_support_confirmation": notes.customer_sentiment == "COOPERATIVE" and any("confirm" in bp.lower() or "travel" in bp.lower() for bp in notes.bullet_points)
        }

        red_flags: List[PolicyFlag] = []
        green_flags: List[PolicyFlag] = []
        score_modifier = 0

        # Safe evaluation of conditions
        for rule in self.rules:
            condition_expr = rule.get("condition", "False")
            try:
                # Evaluate in controlled facts dict
                triggered = eval(condition_expr, {"__builtins__": {}}, facts)
            except Exception:
                triggered = False

            if triggered:
                flag_type = FlagType.RED if rule["flag_type"] == "RED" else FlagType.GREEN
                severity = FlagSeverity(rule.get("severity", "MEDIUM"))
                
                # Build descriptive evidence pointer
                evidence = self._generate_evidence_pointer(rule["id"], facts, alert, profiling, notes)
                
                flag = PolicyFlag(
                    flag_type=flag_type,
                    rule_id=rule["id"],
                    flag_name=rule["name"],
                    severity=severity,
                    description=rule["description"],
                    evidence_pointer=evidence,
                    source_system=rule.get("source", "OFD")
                )
                
                if flag_type == FlagType.RED:
                    red_flags.append(flag)
                    score_modifier += rule.get("score_impact", 15)
                else:
                    green_flags.append(flag)
                    score_modifier += rule.get("score_impact", -15)

        # Calculate calibrated risk score
        base_score = alert.initial_risk_score
        calculated_score = max(5, min(99, base_score + score_modifier))

        # Determine risk level and recommended actions
        if calculated_score >= 80:
            risk_level = "CRITICAL"
            recommended_action = "BLOCK_ACCOUNT"
            action_title = "Immediately Freeze Account & Revoke Online Banking Access"
            urgency = "IMMEDIATE (< 15 mins)"
            sop_ref = "SOP-SEC-802: Account Takeover Emergency Containment"
            rationale = (
                f"Critical risk score ({calculated_score}/100) triggered by {len(red_flags)} policy violations "
                f"including severe device/network divergence. Immediate containment required to halt fund exfiltration."
            )
            alternatives = ["RESTRICT_CARD", "ESCALATE_TIER2"]
        elif calculated_score >= 60:
            risk_level = "HIGH"
            recommended_action = "RESTRICT_CARD"
            action_title = "Place Temporary Restriction on Card / Suspend Outbound Wires"
            urgency = "HIGH (< 1 hour)"
            sop_ref = "SOP-OFD-403: High Velocity & Spend Deviation Response"
            rationale = (
                f"Elevated risk score ({calculated_score}/100). Spend pattern and telemetry exhibit material risk; "
                f"restrict transactional mechanisms pending customer verification."
            )
            alternatives = ["CONTACT_CUSTOMER", "ESCALATE_TIER2"]
        elif calculated_score >= 40:
            risk_level = "MEDIUM"
            recommended_action = "CONTACT_CUSTOMER"
            action_title = "Initiate Outbound Customer Verification Call"
            urgency = "SAME_DAY"
            sop_ref = "SOP-OPS-211: Customer Outreach & Identity Attestation"
            rationale = (
                f"Moderate risk score ({calculated_score}/100). Ambiguous indicators present without definitive compromise. "
                f"Voice or step-up authentication required."
            )
            alternatives = ["RESTRICT_CARD", "DISMISS_ALERT"]
        else:
            risk_level = "LOW"
            recommended_action = "DISMISS_ALERT"
            action_title = "Dismiss Alert as Verified Legitimate Activity (False Positive)"
            urgency = "ROUTINE"
            sop_ref = "SOP-EXEMP-105: Verified Travel & Strong Authentication Exemption"
            rationale = (
                f"Low risk score ({calculated_score}/100). Multiple mitigating green flags present "
                f"({len(green_flags)} verified). Documented travel notice and strong biometric proof confirm legitimate customer intent."
            )
            alternatives = ["CONTACT_CUSTOMER"]

        return PolicyDecisionResult(
            policy_pack=self.policy_name,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
            risk_score=calculated_score,
            risk_level=risk_level,
            red_flags=red_flags,
            green_flags=green_flags,
            recommended_action=recommended_action,
            recommended_action_title=action_title,
            action_urgency=urgency,
            sop_reference=sop_ref,
            decision_rationale=rationale,
            alternative_actions=alternatives
        )

    def _generate_evidence_pointer(
        self,
        rule_id: str,
        facts: Dict[str, Any],
        alert: FraudAlert,
        profiling: CustomerProfilingResult,
        notes: NotesSummarizationResult
    ) -> str:
        if rule_id == "ATO-SOP-101":
            return f"IP: {alert.device_telemetry.ip_address} ({alert.device_telemetry.city}, {alert.device_telemetry.country}) vs Customer Home ({profiling.customer_id})"
        elif rule_id == "OFD-RULE-204":
            return f"Amount: ${alert.trigger_transaction.amount:,.2f} ({profiling.spend_deviation_factor:.1f}x baseline monthly avg)"
        elif rule_id == "DTFR-RULE-305":
            return f"VPN/Proxy: {profiling.is_vpn_detected}, Device Trust Score: {profiling.device_trust_score:.2f}"
        elif rule_id == "RCDV-RULE-401":
            return f"Account age: {profiling.tenure_months} months, 24h tx velocity: {profiling.velocity_24h_count} transactions"
        elif rule_id == "EEDE-RULE-502":
            return f"Wire Channel: Amount ${alert.trigger_transaction.amount:,.2f}, 2FA: {alert.trigger_transaction.two_factor_authenticated}"
        elif rule_id == "ATO-NOTE-603":
            return f"Security events: {', '.join(notes.recent_security_events)}"
        elif rule_id == "GREEN-MIT-01":
            return f"Biometric Match: {alert.device_telemetry.biometric_confidence_score * 100:.0f}% confidence ({alert.trigger_transaction.auth_method})"
        elif rule_id == "GREEN-MIT-02":
            dest = notes.detected_travel_notice.get("destination", "Reported Destination") if notes.detected_travel_notice else "Reported Destination"
            return f"Active Travel Notice: Destination {dest} matched transaction location {alert.device_telemetry.country}"
        elif rule_id == "GREEN-MIT-03":
            return f"Tenure: {profiling.tenure_months} months with 0 confirmed historical fraud cases"
        elif rule_id == "GREEN-MIT-04":
            return "Customer care telephony log indicates verified voice contact"
        return "Aggregated system telemetry match"
