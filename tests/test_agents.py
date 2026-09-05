import pytest
import asyncio
from app.models.alert import FraudAlert, CustomerProfile, Transaction, DeviceTelemetry
from app.agents.profiling_agent import CustomerProfilingAgent
from app.agents.history_agent import CaseHistoryAgent
from app.agents.notes_agent import NotesSummarizationAgent
from app.agents.policy_agent import PolicyDecisionAgent

@pytest.fixture
def sample_alert():
    return FraudAlert(
        alert_id="ALERT-TEST-01",
        alert_type="ATO",
        timestamp="2026-09-05T10:00:00Z",
        rule_name="RULE_ATO_TEST",
        severity="CRITICAL",
        customer_id="CUST-TEST-99",
        account_number="ACT-TEST-1234",
        trigger_transaction=Transaction(
            transaction_id="TX-TEST-01",
            timestamp="2026-09-05T09:59:00Z",
            amount=5000.0,
            merchant_name="CryptoGlobal Ltd",
            merchant_category_code="6051",
            channel="WIRE",
            is_card_present=False,
            two_factor_authenticated=False
        ),
        device_telemetry=DeviceTelemetry(
            ip_address="102.89.23.11",
            device_id="DEV-LINUX-TEST",
            device_os="Linux",
            country="NG",
            city="Lagos",
            is_vpn_or_proxy=True,
            is_new_device=True,
            biometric_confidence_score=0.10
        ),
        trigger_reason="Test foreign wire on new device",
        initial_risk_score=85
    )

@pytest.fixture
def sample_customer():
    return CustomerProfile(
        customer_id="CUST-TEST-99",
        full_name="Alice Smith",
        email="alice@example.com",
        phone="+1-312-555-1234",
        account_number="ACT-TEST-1234",
        account_tenure_months=24,
        kyc_status="VERIFIED",
        risk_tier="LOW",
        registered_city="Chicago",
        registered_state="IL",
        avg_monthly_volume_usd=3000.0,
        active_cards=["CARD-001"]
    )

@pytest.mark.asyncio
async def test_cust_profiling_agent(sample_customer, sample_alert):
    agent = CustomerProfilingAgent()
    result = await agent.profile_customer(sample_customer, sample_alert)
    
    assert result.customer_id == sample_customer.customer_id
    assert result.is_foreign_ip is True
    assert result.is_vpn_detected is True
    assert result.spend_deviation_factor > 1.0
    assert result.geolocation_distance_miles > 1000.0
    assert result.device_trust_score < 0.5
    assert len(result.linked_systems_consulted) > 5

@pytest.mark.asyncio
async def test_case_history_agent(sample_customer, sample_alert):
    agent = CaseHistoryAgent()
    raw_history = [
        {
            "case_id": "HIST-01",
            "date": "2024-01-01",
            "alert_type": "POS_ANOMALY",
            "disposition": "FALSE_POSITIVE",
            "loss_amount_usd": 0.0,
            "summary": "Legitimate card swipe.",
            "system_origin": "CRA"
        }
    ]
    result = await agent.fetch_history(sample_customer, sample_alert, raw_history)
    
    assert result.total_prior_cases == 1
    assert result.false_positive_count == 1
    assert result.confirmed_fraud_count == 0
    assert len(result.systems_consulted) >= 3

@pytest.mark.asyncio
async def test_notes_summarization_agent(sample_customer, sample_alert):
    agent = NotesSummarizationAgent()
    raw_notes = [
        {
            "source": "PCFD",
            "timestamp": "2026-09-04T12:00:00Z",
            "text": "Customer reported phishing email with password reset link.",
            "sentiment": "DISTRESSED"
        },
        {
            "source": "CRM_Notes",
            "timestamp": "2026-09-05T02:00:00Z",
            "text": "Password reset completed via self-service portal.",
            "sentiment": "NEUTRAL"
        }
    ]
    result = await agent.summarize_notes(sample_customer, sample_alert, raw_notes)
    
    assert result.total_notes_analyzed == 2
    assert len(result.bullet_points) >= 2
    assert len(result.recent_security_events) >= 1
    assert result.customer_sentiment == "DISTRESSED"

@pytest.mark.asyncio
async def test_policy_decision_agent(sample_customer, sample_alert):
    prof_agent = CustomerProfilingAgent()
    hist_agent = CaseHistoryAgent()
    notes_agent = NotesSummarizationAgent()
    policy_agent = PolicyDecisionAgent()

    prof_res = await prof_agent.profile_customer(sample_customer, sample_alert)
    hist_res = await hist_agent.fetch_history(sample_customer, sample_alert, [])
    notes_res = await notes_agent.summarize_notes(sample_customer, sample_alert, [
        {"source": "PCFD", "text": "Password reset done.", "sentiment": "DISTRESSED"}
    ])

    policy_res = await policy_agent.evaluate_policy(sample_alert, prof_res, hist_res, notes_res)

    assert policy_res.risk_score >= 80
    assert policy_res.risk_level == "CRITICAL"
    assert policy_res.recommended_action == "BLOCK_ACCOUNT"
    assert len(policy_res.red_flags) >= 2
    assert any(rf.rule_id == "ATO-SOP-101" for rf in policy_res.red_flags)
