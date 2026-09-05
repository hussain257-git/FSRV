import logging
from typing import List, Dict, Any, Optional
from app.models.agent_results import CaseHistoryResult, HistoricalCase
from app.models.alert import FraudAlert, CustomerProfile
from app.masking import PIIMasker
from app.tachyon_client_pool import tachyon_pool
from app.audit_store import audit_store

logger = logging.getLogger("agent.history")

class CaseHistoryAgent:
    """
    Case History Agent (Image 1 & 3 in Enterprise Architecture):
    - Input: ECN (Enterprise Customer Number)
    - Primary DB: Oracle case tables / case_context.db
    - LLM: gpt5.1 (via Tachyon ADK Client)
    - Output Style: Bullet-point summary
    - Stateless: Yes
    - Data Flow:
        ECN -> DB fetch -> API call -> Mask -> LLM (gpt5.1) -> Parse bullets -> Return grouped
    """
    def __init__(self):
        self.name = "Case History Agent"
        self.model = "gpt5.1 (Tachyon)"
        self.systems = ["Oracle_CRA", "Orig", "TFS", "FraudNet"]

    async def fetch_history(
        self,
        customer: CustomerProfile,
        alert: FraudAlert,
        raw_history_records: List[Dict[str, Any]] = None
    ) -> CaseHistoryResult:
        ecn = customer.customer_id
        logger.info(f"[{self.name}] Querying case history for ECN: {ecn}")

        cases: List[HistoricalCase] = []
        if raw_history_records:
            for r in raw_history_records:
                cases.append(HistoricalCase(
                    case_id=r.get("case_id", "HIST-UNK"),
                    date=r.get("date", "2025-01-01"),
                    alert_type=r.get("alert_type", "GENERAL_ALERT"),
                    disposition=r.get("disposition", "RESOLVED"),
                    loss_amount_usd=float(r.get("loss_amount_usd", 0.0)),
                    summary=r.get("summary", ""),
                    system_origin=r.get("system_origin", "Oracle_CRA")
                ))

        # PII Masking stage before LLM call
        raw_payload = {
            "ecn": ecn,
            "tenure_months": customer.account_tenure_months,
            "raw_cases": [c.model_dump() for c in cases]
        }
        masked_payload, tokens = PIIMasker.mask_payload(raw_payload)

        # Call LLM (gpt5.1 via Tachyon Client Pool)
        llm_prompt = (
            f"Analyze historical fraud and dispute cases for ECN {masked_payload.get('ecn')}.\n"
            f"Historical records: {masked_payload.get('raw_cases')}\n"
            f"Provide a 3-bullet concise synthesis of customer claim reliability and prior losses."
        )
        llm_summary = await tachyon_pool.call_model(
            model_name="gpt5.1",
            prompt=llm_prompt,
            system_instructions="You are an enterprise financial crime case history analyst."
        )

        # Audit store record
        audit_store.record_event(
            case_id=f"CASE-{alert.alert_id.replace('ALERT-', '')}",
            agent_name=self.name,
            action_type="HISTORY_FETCHED_AND_SYNTHESIZED",
            payload_summary=f"ECN {ecn} parsed via {self.model} with {len(cases)} historical cases."
        )

        confirmed_fraud = sum(1 for c in cases if c.disposition == "CONFIRMED_FRAUD")
        false_positives = sum(1 for c in cases if c.disposition in ["FALSE_POSITIVE", "DISMISSED"])
        total_disputed = sum(c.loss_amount_usd for c in cases)

        if not cases:
            summary = f"Customer has a clean historical record with 0 prior alerts or dispute filings in CRA/TFS."
        elif confirmed_fraud > 0:
            summary = (
                f"Customer record shows {len(cases)} prior case(s) with {confirmed_fraud} CONFIRMED FRAUD disposition(s). "
                f"Total cumulative loss: ₹{total_disputed:,.2f}. Heightened monitoring recommended."
            )
        else:
            summary = (
                f"Customer record shows {len(cases)} prior case(s), all resolved as FALSE_POSITIVE or DISMISSED. "
                f"High baseline reliability indicated."
            )

        return CaseHistoryResult(
            customer_id=customer.customer_id,
            total_prior_cases=len(cases),
            confirmed_fraud_count=confirmed_fraud,
            false_positive_count=false_positives,
            total_disputed_amount_usd=round(total_disputed, 2),
            recent_cases=cases[:3],
            account_relationship_summary=summary,
            systems_consulted=self.systems
        )
