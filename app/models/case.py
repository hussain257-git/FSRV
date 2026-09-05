from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from .alert import FraudAlert, CustomerProfile
from .agent_results import (
    CustomerProfilingResult,
    CaseHistoryResult,
    NotesSummarizationResult,
    PolicyDecisionResult,
)

class CaseStatus(str, Enum):
    NEW = "NEW"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    RESOLVED_BLOCKED = "RESOLVED_BLOCKED"
    RESOLVED_RESTRICTED = "RESOLVED_RESTRICTED"
    RESOLVED_DISMISSED = "RESOLVED_DISMISSED"
    ESCALATED = "ESCALATED"

class AuditLogEntry(BaseModel):
    timestamp: str
    actor: str  # Orchestrator, InvestigationAgent, CustProfilingAgent, PolicyDecisionAgent, Analyst
    action: str
    details: str
    metadata: Optional[Dict[str, Any]] = None

class ConsolidatedSummary(BaseModel):
    headline: str
    risk_assessment: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    key_findings: List[str]
    case_beginning: Optional[List[str]] = None
    key_events_happened: Optional[List[str]] = None
    suggested_investigator_script: Optional[str] = None
    next_step_plan: List[str]

class CaseRecord(BaseModel):
    case_id: str
    created_at: str
    updated_at: str
    status: CaseStatus = CaseStatus.NEW
    assigned_analyst: Optional[str] = "OFD Case Analyst"
    alert: FraudAlert
    customer_profile: CustomerProfile
    profiling_result: Optional[CustomerProfilingResult] = None
    history_result: Optional[CaseHistoryResult] = None
    notes_result: Optional[NotesSummarizationResult] = None
    policy_result: Optional[PolicyDecisionResult] = None
    consolidated_summary: Optional[ConsolidatedSummary] = None
    audit_trail: List[AuditLogEntry] = []
    investigation_duration_ms: Optional[float] = None
