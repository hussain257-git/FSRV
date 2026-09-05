import logging
from app.models.alert import FraudAlert
from app.models.agent_results import (
    CustomerProfilingResult,
    CaseHistoryResult,
    NotesSummarizationResult,
    PolicyDecisionResult
)
from app.policy_engine.engine import PolicyRuleEngine
from app.masking import PIIMasker
from app.tachyon_client_pool import tachyon_pool
from app.audit_store import audit_store

logger = logging.getLogger("agent.policy")

class PolicyDecisionAgent:
    """
    Policy Decision Agent (Image 1 & 3 in Enterprise Architecture):
    - Input: Case data + analysis payload
    - Primary DB: SQLite sessions + policy rules (sop_actions_2.db)
    - LLM: gpt5.1 (via Tachyon ADK Client)
    - Output Style: Structured flags + recommendation
    - Stateless: Yes (context per request)
    - Data Flow:
        Payload -> Load rules -> Route by tool -> Parallel sub-agents -> Mask
        -> Parent LLM merge -> Rank decision -> Return
    """
    def __init__(self):
        self.name = "Policy Decision Agent"
        self.model = "gpt5.1 (Tachyon)"
        self.engine = PolicyRuleEngine()

    async def evaluate_policy(
        self,
        alert: FraudAlert,
        profiling: CustomerProfilingResult,
        history: CaseHistoryResult,
        notes: NotesSummarizationResult
    ) -> PolicyDecisionResult:
        logger.info(f"[{self.name}] Applying policy rules & LLM decision synthesis for alert {alert.alert_id}")

        # 1. Rule Engine evaluation (Deterministic SOP baseline)
        decision = self.engine.evaluate(
            alert=alert,
            profiling=profiling,
            history=history,
            notes=notes
        )

        # 2. PII Masking stage before Parent LLM call
        case_summary_payload = {
            "alert_id": alert.alert_id,
            "amount": alert.trigger_transaction.amount,
            "currency": alert.trigger_transaction.currency,
            "channel": alert.trigger_transaction.channel,
            "red_flags": [f.model_dump() for f in decision.red_flags],
            "green_flags": [f.model_dump() for f in decision.green_flags]
        }
        masked_payload, tokens = PIIMasker.mask_payload(case_summary_payload)

        # 3. Parent LLM merge & decision validation (gpt5.1 via Tachyon Pool)
        llm_prompt = (
            f"Review policy decision payload for case: {masked_payload}\n"
            f"Evaluated SOP: {decision.sop_reference}\n"
            f"Recommended Action: {decision.recommended_action} ({decision.recommended_action_title})\n"
            f"Confirm decision ranking and provide final executive risk verdict."
        )
        llm_verdict = await tachyon_pool.call_model(
            model_name="gpt5.1",
            prompt=llm_prompt,
            system_instructions="You are the Parent Policy Decision Arbiter for Bank Fraud Operations."
        )

        # 4. Record to immutable audit store
        audit_store.record_event(
            case_id=f"CASE-{alert.alert_id.replace('ALERT-', '')}",
            agent_name=self.name,
            action_type="POLICY_EVALUATED_AND_RANKED",
            payload_summary=f"SOP {decision.sop_reference} evaluated via {self.model}. Risk Score: {decision.risk_score}."
        )

        return decision
