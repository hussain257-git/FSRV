from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel

class AnalystActionType(str, Enum):
    BLOCK_ACCOUNT = "BLOCK_ACCOUNT"
    RESTRICT_CARD = "RESTRICT_CARD"
    CONTACT_CUSTOMER = "CONTACT_CUSTOMER"
    ESCALATE_TIER2 = "ESCALATE_TIER2"
    DISMISS_FALSE_POSITIVE = "DISMISS_FALSE_POSITIVE"
    ADD_CASE_NOTE = "ADD_CASE_NOTE"

class AnalystActionRequest(BaseModel):
    action_type: AnalystActionType
    analyst_id: str = "OFD-ANALYST-409"
    analyst_name: str = "Sarah Jenkins"
    investigator_notes: str
    override_reason: Optional[str] = None

class AnalystActionResponse(BaseModel):
    case_id: str
    action_type: AnalystActionType
    status: str
    message: str
    recorded_at: str
    audit_entry_id: str
