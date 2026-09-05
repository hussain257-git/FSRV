import pytest
import time
from app.database import CaseDatabase
from app.agents.orchestrator import CaseOrchestratorAgent
from app.models.alert import FraudAlert, CustomerProfile
from app.models.case import CaseStatus

@pytest.mark.asyncio
async def test_case_orchestrator_end_to_end():
    db = CaseDatabase()
    orchestrator = CaseOrchestratorAgent(db)
    
    seed_scenarios = db.get_seed_data()
    assert len(seed_scenarios) >= 4

    # Test orchestration on first scenario (ATO)
    sc = seed_scenarios[0]
    alert = FraudAlert(**sc["alert"])
    customer = CustomerProfile(**sc["customer"])

    start_time = time.perf_counter()
    case = await orchestrator.handle_fraud_alert(
        alert=alert,
        customer=customer,
        raw_history=sc.get("raw_history", []),
        raw_notes=sc.get("raw_notes", [])
    )
    elapsed_seconds = time.perf_counter() - start_time

    # Performance SLA: must complete in under 3.0 seconds (typically < 0.1s in prototype)
    assert elapsed_seconds < 3.0
    print(f"End-to-End Orchestration Turnaround: {elapsed_seconds * 1000:.1f}ms")

    # Verify case state and outputs
    assert case.status == CaseStatus.READY_FOR_REVIEW
    assert case.case_id == f"CASE-{alert.alert_id.replace('ALERT-', '')}"
    assert case.profiling_result is not None
    assert case.history_result is not None
    assert case.notes_result is not None
    assert case.policy_result is not None
    assert case.consolidated_summary is not None
    assert case.consolidated_summary.confidence_score >= 0.85
    assert len(case.consolidated_summary.key_findings) >= 3
    assert len(case.consolidated_summary.next_step_plan) >= 2

    # Verify audit trail contains complete agent timeline
    actors = [entry.actor for entry in case.audit_trail]
    assert "Case Orchestrator Agent" in actors
    assert "Investigation Agent" in actors
    assert "Cust Profiling Agent" in actors
    assert "Case History Agent" in actors
    assert "Notes Summarization Agent" in actors
    assert "Policy Decision Agent" in actors

    # Verify persistence in DB
    retrieved = db.get_case(case.case_id)
    assert retrieved is not None
    assert retrieved.case_id == case.case_id
