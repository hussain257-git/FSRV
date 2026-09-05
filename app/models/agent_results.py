from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class FlagSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class FlagType(str, Enum):
    RED = "RED"
    GREEN = "GREEN"

class PolicyFlag(BaseModel):
    flag_type: FlagType  # RED or GREEN
    rule_id: str
    flag_name: str
    severity: FlagSeverity
    description: str
    evidence_pointer: str  # e.g., "Telemetry: IP Lagos, Nigeria vs Reg: Chicago, IL"
    source_system: str     # OFD, ATO, EEDE, FPF, DTFR, RCDV

class CustomerProfilingResult(BaseModel):
    customer_id: str
    account_number: str
    tenure_months: int
    kyc_status: str
    kyc_verified: bool
    risk_rating: str
    velocity_24h_count: int
    velocity_24h_amount_usd: float
    spend_deviation_factor: float  # e.g., 4.5x normal spend
    geolocation_distance_miles: float
    is_foreign_ip: bool
    is_vpn_detected: bool
    device_trust_score: float  # 0.0 to 1.0
    linked_systems_consulted: List[str] = [
        "ECPR", "OPS", "DPMS", "DCBS", "FSRV", "IDAD", "TMS", "OAT"
    ]
    profiling_summary: str

class HistoricalCase(BaseModel):
    case_id: str
    date: str
    alert_type: str
    disposition: str  # CONFIRMED_FRAUD, FALSE_POSITIVE, CUSTOMER_DISPUTE_WON, DISMISSED
    loss_amount_usd: float
    summary: str
    system_origin: str  # CRA, Orig, TFS

class CaseHistoryResult(BaseModel):
    customer_id: str
    total_prior_cases: int
    confirmed_fraud_count: int
    false_positive_count: int
    total_disputed_amount_usd: float
    recent_cases: List[HistoricalCase]
    account_relationship_summary: str
    systems_consulted: List[str] = ["CRA", "Orig", "TFS"]

class NotesSummarizationResult(BaseModel):
    customer_id: str
    total_notes_analyzed: int
    bullet_points: List[str]
    detected_travel_notice: Optional[Dict[str, Any]] = None
    recent_security_events: List[str] = []
    customer_sentiment: str  # COOPERATIVE, DISTRESSED, SUSPICIOUS, UNRESPONSIVE
    systems_consulted: List[str] = ["PCFD", "Pindrop", "CRM_Notes"]

class PolicyDecisionResult(BaseModel):
    policy_pack: str = "OFD_GLOBAL_SOP_v2.4"
    evaluated_at: str
    risk_score: int = Field(ge=0, le=100)
    risk_level: str  # CRITICAL, HIGH, MEDIUM, LOW
    red_flags: List[PolicyFlag] = []
    green_flags: List[PolicyFlag] = []
    recommended_action: str  # BLOCK_ACCOUNT, RESTRICT_CARD, CONTACT_CUSTOMER, ESCALATE_TIER2, DISMISS_ALERT
    recommended_action_title: str
    action_urgency: str  # IMMEDIATE (<15m), SAME_DAY, ROUTINE
    sop_reference: str
    decision_rationale: str
    alternative_actions: List[str] = []
