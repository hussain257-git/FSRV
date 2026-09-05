from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class DeviceTelemetry(BaseModel):
    ip_address: str
    device_id: str
    device_os: Optional[str] = "Unknown"
    browser: Optional[str] = "Unknown"
    country: str = "US"
    city: str = "New York"
    is_vpn_or_proxy: bool = False
    is_new_device: bool = False
    biometric_confidence_score: Optional[float] = 0.95

class Transaction(BaseModel):
    transaction_id: str
    timestamp: str
    amount: float
    currency: str = "USD"
    merchant_name: str
    merchant_category_code: str
    channel: str  # WIRE, ONLINE_CHECKOUT, P2P, ATM, POS
    is_card_present: bool = False
    two_factor_authenticated: bool = False
    auth_method: Optional[str] = "SMS_OTP"  # SMS_OTP, BIOMETRIC, APP_PUSH, NONE

class CustomerProfile(BaseModel):
    customer_id: str
    full_name: str
    email: str
    phone: str
    account_number: str
    account_type: str = "Checking"  # Checking, Savings, Premium
    account_tenure_months: int = 24
    kyc_status: str = "VERIFIED"
    risk_tier: str = "LOW"  # LOW, MEDIUM, HIGH
    registered_city: str = "Chicago"
    registered_state: str = "IL"
    avg_monthly_volume_usd: float = 3500.0
    active_cards: List[str] = []

class FraudAlert(BaseModel):
    alert_id: str
    alert_type: str  # ATO, CNP_SPREE, WIRE_ANOMALY, MULE_RAPID_MOVEMENT, TRAVEL_SUSPICION
    timestamp: str
    rule_name: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    customer_id: str
    account_number: str
    trigger_transaction: Transaction
    device_telemetry: DeviceTelemetry
    trigger_reason: str
    initial_risk_score: int = Field(ge=0, le=100)
