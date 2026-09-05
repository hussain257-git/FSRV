import math
import logging
from typing import Dict, Any, List
from app.models.alert import FraudAlert, CustomerProfile, DeviceTelemetry
from app.models.agent_results import CustomerProfilingResult

logger = logging.getLogger("agent.profiling")

class CustomerProfilingAgent:
    """
    Step 4 in Architecture: Plans and fetches customer profiling, KYC, 
    account telemetry, and transactional velocity across enterprise systems
    (ECPR, OPS, DPMS, DCBS, FSRV, IDAD, RISE, CCBS, SIMS, TMS, OAT, APS, GCI).
    """
    def __init__(self):
        self.name = "Cust Profiling Agent"
        self.systems = [
            "ECPR", "OPS", "DPMS", "DCBS", "FSRV", 
            "IDAD", "RISE", "CCBS", "SIMS", "TMS", "OAT", "APS", "GCI"
        ]

    async def profile_customer(
        self,
        customer: CustomerProfile,
        alert: FraudAlert
    ) -> CustomerProfilingResult:
        logger.info(f"[{self.name}] Initiating profiling for customer {customer.customer_id}")

        # Compute spend deviation factor
        avg_monthly = max(customer.avg_monthly_volume_usd, 1.0)
        expected_single_tx_norm = avg_monthly / 15.0  # Approx norm per transaction
        tx_amount = alert.trigger_transaction.amount
        spend_deviation_factor = round(tx_amount / expected_single_tx_norm, 2)

        # Evaluate foreign / geographic divergence
        is_foreign = alert.device_telemetry.country.upper() != "US"
        
        # Calculate simulated distance hop in miles based on city/country
        distance_miles = self._calculate_geo_distance(
            customer.registered_city,
            customer.registered_state,
            alert.device_telemetry.city,
            alert.device_telemetry.country
        )

        # Determine device trust score
        base_trust = 0.90
        if alert.device_telemetry.is_new_device:
            base_trust -= 0.40
        if alert.device_telemetry.is_vpn_or_proxy:
            base_trust -= 0.35
        if is_foreign:
            base_trust -= 0.15
        device_trust_score = max(0.05, round(base_trust, 2))

        # Velocity metrics (simulated from TMS / DPMS telemetry)
        velocity_count = 1
        velocity_amount = tx_amount
        if alert.alert_type in ["CNP_SPREE", "MULE_RAPID_MOVEMENT"]:
            velocity_count = 4
            velocity_amount = tx_amount * 3.2

        summary = (
            f"Customer {customer.full_name} (Tenure: {customer.account_tenure_months} mos, KYC: {customer.kyc_status}). "
            f"Current transaction of ${tx_amount:,.2f} is {spend_deviation_factor}x normal transaction baseline. "
            f"Originated from {alert.device_telemetry.city}, {alert.device_telemetry.country} "
            f"({distance_miles:,.0f} miles from home: {customer.registered_city}, {customer.registered_state}). "
            f"Device trust: {device_trust_score * 100:.0f}%, VPN: {alert.device_telemetry.is_vpn_or_proxy}."
        )

        return CustomerProfilingResult(
            customer_id=customer.customer_id,
            account_number=customer.account_number,
            tenure_months=customer.account_tenure_months,
            kyc_status=customer.kyc_status,
            kyc_verified=(customer.kyc_status.upper() == "VERIFIED"),
            risk_rating=customer.risk_tier,
            velocity_24h_count=velocity_count,
            velocity_24h_amount_usd=round(velocity_amount, 2),
            spend_deviation_factor=spend_deviation_factor,
            geolocation_distance_miles=distance_miles,
            is_foreign_ip=is_foreign,
            is_vpn_detected=alert.device_telemetry.is_vpn_or_proxy,
            device_trust_score=device_trust_score,
            linked_systems_consulted=self.systems,
            profiling_summary=summary
        )

    def _calculate_geo_distance(self, reg_city: str, reg_state: str, cur_city: str, cur_country: str) -> float:
        if cur_country.upper() != "US":
            if cur_country.upper() in ["NG", "NIGERIA"]:
                return 5820.0
            elif cur_country.upper() in ["FR", "FRANCE"]:
                return 4150.0
            elif cur_country.upper() in ["RU", "RUSSIA", "CN", "CHINA"]:
                return 6200.0
            return 4500.0
        
        if reg_city.lower() == cur_city.lower():
            return 8.5  # Local metro hop
        return 850.0  # Domestic interstate hop
