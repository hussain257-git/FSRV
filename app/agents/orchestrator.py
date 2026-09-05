import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.models.alert import FraudAlert, CustomerProfile
from app.models.case import CaseRecord, CaseStatus, AuditLogEntry
from app.models.actions import AnalystActionRequest, AnalystActionResponse
from app.agents.investigation import InvestigationAgent
from app.database import CaseDatabase

logger = logging.getLogger("agent.orchestrator")

class CaseOrchestratorAgent:
    """
    Top-Level Orchestrator (Steps 1, 2, 8, 9, 11 in Architecture):
    - Receives published fraud alert (Step 1).
    - Creates case in Case DB (Step 2).
    - Triggers offline investigation via Investigation Agent (Step 3).
    - Persists analysis, Red/Green flags, and next steps to Case DB (Step 8, 9).
    - Exposes case data and recommendations to PREVENT UI (Step 11).
    - Records analyst decisions in immutable audit trail (Step 12).
    """
    def __init__(self, db: CaseDatabase):
        self.name = "Case Orchestrator Agent"
        self.db = db
        self.investigation_agent = InvestigationAgent()

    async def handle_fraud_alert(
        self,
        alert: FraudAlert,
        customer: CustomerProfile,
        raw_history: List[Dict[str, Any]] = None,
        raw_notes: List[Dict[str, Any]] = None
    ) -> CaseRecord:
        start_time = time.perf_counter()
        case_id = f"CASE-{alert.alert_id.replace('ALERT-', '')}"
        now_str = datetime.now(timezone.utc).isoformat()

        logger.info(f"[{self.name}] Ingesting alert {alert.alert_id}. Creating case {case_id}")

        # Step 2: Create initial case record in DB
        initial_case = CaseRecord(
            case_id=case_id,
            created_at=now_str,
            updated_at=now_str,
            status=CaseStatus.UNDER_INVESTIGATION,
            assigned_analyst="OFD Case Analyst",
            alert=alert,
            customer_profile=customer,
            audit_trail=[
                AuditLogEntry(
                    timestamp=now_str,
                    actor=self.name,
                    action="CASE_CREATED",
                    details=f"Alert {alert.alert_id} ({alert.alert_type}) ingested into Case DB."
                )
            ]
        )
        self.db.save_case(initial_case)

        # Step 3: Trigger offline agentic investigation
        logger.info(f"[{self.name}] Triggering offline agentic investigation for {case_id}")
        (
            profiling,
            history,
            notes,
            policy,
            summary,
            agent_audits
        ) = await self.investigation_agent.conduct_investigation(
            alert=alert,
            customer=customer,
            raw_history=raw_history,
            raw_notes=raw_notes
        )

        total_elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Step 8 & 9: Persist complete analysis and next steps to Case DB
        updated_case = self.db.get_case(case_id)
        if not updated_case:
            updated_case = initial_case

        updated_case.updated_at = datetime.now(timezone.utc).isoformat()
        updated_case.status = CaseStatus.READY_FOR_REVIEW
        updated_case.profiling_result = profiling
        updated_case.history_result = history
        updated_case.notes_result = notes
        updated_case.policy_result = policy
        updated_case.consolidated_summary = summary
        updated_case.investigation_duration_ms = round(total_elapsed_ms, 2)

        # Append audit events
        for entry in agent_audits:
            updated_case.audit_trail.append(entry)

        updated_case.audit_trail.append(AuditLogEntry(
            timestamp=updated_case.updated_at,
            actor=self.name,
            action="ANALYSIS_PERSISTED",
            details=f"Consolidated investigation results persisted. Turnaround: {total_elapsed_ms:.1f}ms. Status -> READY_FOR_REVIEW."
        ))

        self.db.save_case(updated_case)
        logger.info(f"[{self.name}] Case {case_id} fully orchestrated and ready for analyst in {total_elapsed_ms:.1f}ms")
        return updated_case

    async def execute_analyst_action(
        self,
        case_id: str,
        action_request: AnalystActionRequest
    ) -> AnalystActionResponse:
        case = self.db.get_case(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found in database.")

        now_str = datetime.now(timezone.utc).isoformat()
        action_type = action_request.action_type.value

        # Map action to new case status
        if action_type == "BLOCK_ACCOUNT":
            new_status = CaseStatus.RESOLVED_BLOCKED
            desc = "Account frozen, debit cards locked, and online banking credentials revoked."
        elif action_type == "RESTRICT_CARD":
            new_status = CaseStatus.RESOLVED_RESTRICTED
            desc = "Outbound card transactions blocked. Step-up 2FA requested."
        elif action_type == "DISMISS_FALSE_POSITIVE":
            new_status = CaseStatus.RESOLVED_DISMISSED
            desc = "Alert dismissed as confirmed legitimate activity. False positive recorded for tuning."
        elif action_type == "ESCALATE_TIER2":
            new_status = CaseStatus.ESCALATED
            desc = "Case escalated to Senior Financial Crimes / AML Unit for forensic wire trace."
        elif action_type == "CONTACT_CUSTOMER":
            new_status = CaseStatus.UNDER_INVESTIGATION
            desc = "Outbound contact workflow initiated. Awaiting customer confirmation."
        else:
            new_status = case.status
            desc = f"Analyst note added: {action_request.investigator_notes}"

        case.status = new_status
        case.updated_at = now_str
        case.assigned_analyst = action_request.analyst_name

        audit_entry_id = f"AUDIT-{int(time.time() * 1000)}"
        case.audit_trail.append(AuditLogEntry(
            timestamp=now_str,
            actor=f"{action_request.analyst_name} ({action_request.analyst_id})",
            action=action_type,
            details=f"{desc} Analyst Notes: '{action_request.investigator_notes}'",
            metadata={"override_reason": action_request.override_reason}
        ))

        self.db.save_case(case)

        return AnalystActionResponse(
            case_id=case_id,
            action_type=action_request.action_type,
            status=new_status.value,
            message=f"Action '{action_type}' successfully executed and recorded.",
            recorded_at=now_str,
            audit_entry_id=audit_entry_id
        )
