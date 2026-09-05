import pytest
from app.models.alert import FraudAlert, Transaction, DeviceTelemetry
from app.models.agent_results import (
    CustomerProfilingResult,
    CaseHistoryResult,
    NotesSummarizationResult,
    FlagType
)
from app.policy_engine.engine import PolicyRuleEngine

@pytest.fixture
def policy_engine():
    return PolicyRuleEngine()

def test_travel_exemption_green_flags(policy_engine):
    # Setup a scenario where travel notice and strong biometrics mitigate the risk
    alert = FraudAlert(
        alert_id="ALERT-FP-01",
        alert_type="TRAVEL_SUSPICION",
        timestamp="2026-09-05T12:00:00Z",
        rule_name="RULE_CROSS_BORDER",
        severity="LOW",
        customer_id="CUST-VIP-01",
        account_number="ACT-001",
        trigger_transaction=Transaction(
            transaction_id="TX-01",
            timestamp="2026-09-05T12:00:00Z",
            amount=2500.0,
            merchant_name="Hotel Ritz Paris",
            merchant_category_code="7011",
            channel="POS",
            is_card_present=True,
            two_factor_authenticated=True,
            auth_method="BIOMETRIC"
        ),
        device_telemetry=DeviceTelemetry(
            ip_address="194.254.60.1",
            device_id="DEV-IPHONE-01",
            country="FR",
            city="Paris",
            is_vpn_or_proxy=False,
            is_new_device=False,
            biometric_confidence_score=0.98
        ),
        trigger_reason="Cross-border POS charge",
        initial_risk_score=35
    )

    profiling = CustomerProfilingResult(
        customer_id="CUST-VIP-01",
        account_number="ACT-001",
        tenure_months=48,
        kyc_status="VERIFIED",
        kyc_verified=True,
        risk_rating="LOW",
        velocity_24h_count=1,
        velocity_24h_amount_usd=2500.0,
        spend_deviation_factor=1.2,
        geolocation_distance_miles=4100.0,
        is_foreign_ip=True,
        is_vpn_detected=False,
        device_trust_score=0.95,
        linked_systems_consulted=["ECPR", "OPS"],
        profiling_summary="Low risk established VIP customer"
    )

    history = CaseHistoryResult(
        customer_id="CUST-VIP-01",
        total_prior_cases=1,
        confirmed_fraud_count=0,
        false_positive_count=1,
        total_disputed_amount_usd=0.0,
        recent_cases=[],
        account_relationship_summary="Clean record with 48 mos tenure"
    )

    notes = NotesSummarizationResult(
        customer_id="CUST-VIP-01",
        total_notes_analyzed=2,
        bullet_points=[
            "Customer notified concierge of travel to France.",
            "Voice biometrics confirmed customer identity with 99% score."
        ],
        detected_travel_notice={"destination": "France", "timestamp": "Recent"},
        recent_security_events=[],
        customer_sentiment="COOPERATIVE"
    )

    result = policy_engine.evaluate(alert, profiling, history, notes)

    # Green flags should be triggered
    green_flags = [f for f in result.green_flags if f.flag_type == FlagType.GREEN]
    assert len(green_flags) >= 2
    assert any(gf.rule_id == "GREEN-MIT-01" for gf in green_flags)  # Biometric match
    assert any(gf.rule_id == "GREEN-MIT-02" for gf in green_flags)  # Travel notice match
    assert any(gf.rule_id == "GREEN-MIT-03" for gf in green_flags)  # Long clean tenure

    # Recommended action should be DISMISS_ALERT
    assert result.recommended_action == "DISMISS_ALERT"
    assert result.risk_level == "LOW"
    assert result.risk_score < 40
