from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.agents.policy_chat import PolicyChatAgent

router = APIRouter(prefix="/chat", tags=["Policy Chat"])
policy_chat_agent = PolicyChatAgent()

class ChatMessageRequest(BaseModel):
    ai_case_id: str
    message: str

class ChatMessageResponse(BaseModel):
    ai_case_id: str
    sender: str
    content: str
    timestamp: str
    model_used: Optional[str] = "gemini-2.5-pro (Tachyon)"
    pii_masked: bool = True

@router.post("", response_model=ChatMessageResponse)
async def send_chat_message(chat_req: ChatMessageRequest, request: Request):
    """
    Policy Chat Endpoint (Image 1 & 3 in Enterprise Architecture):
    ai_case_id + message -> Load case + history -> Retrieve policy chunks -> Mask -> LLM (gemini) -> Store in DB -> Return
    """
    orchestrator = request.app.state.orchestrator
    case = orchestrator.db.get_case(chat_req.ai_case_id)
    case_summary = case.consolidated_summary.headline if (case and case.consolidated_summary) else None

    response = await policy_chat_agent.chat(
        ai_case_id=chat_req.ai_case_id,
        user_message=chat_req.message,
        case_summary=case_summary
    )
    return response

@router.get("/{ai_case_id}/history", response_model=List[Dict[str, Any]])
async def get_case_chat_history(ai_case_id: str):
    """
    Retrieves full conversation history from policy_chat_history.db.
    """
    return policy_chat_agent.get_chat_history(ai_case_id)
