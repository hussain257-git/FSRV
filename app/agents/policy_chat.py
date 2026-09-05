import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.db import db_manager
from app.masking import PIIMasker
from app.tachyon_client_pool import tachyon_pool
from app.audit_store import audit_store
from app.config import BASE_DIR

logger = logging.getLogger("agent.policy_chat")

class PolicyChatAgent:
    """
    Policy Chat Agent (Image 1 & 3 in Enterprise Architecture):
    - Input: ai_case_id + user message
    - Primary DB: policy_chat_history.db + case context
    - LLM: gemini-2.5-pro (via Tachyon ADK Client)
    - Output Style: Conversational Q&A
    - Stateful: Maintains conversational history across turns
    - Data Flow:
        ai_case_id + message -> Load case + history -> Retrieve policy chunks
        -> Mask PII -> LLM (gemini) -> Store in DB -> Return
    """
    def __init__(self):
        self.model = "gemini-2.5-pro (Tachyon)"
        self.instructions_file = BASE_DIR / "policy_ofd_instructions.md"
        self._policy_chunks = self._load_policy_chunks()

    def _load_policy_chunks(self) -> str:
        if self.instructions_file.exists():
            try:
                return self.instructions_file.read_text(encoding="utf-8")
            except Exception as e:
                logger.error(f"Failed to read policy instructions: {e}")
        return "Bank OFD standard policies: SOP-SEC-802 (ATO Containment), SOP-EXEMP-105 (Travel Exemption)."

    async def chat(
        self,
        ai_case_id: str,
        user_message: str,
        case_summary: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(f"[Policy Chat] Processing analyst question for case {ai_case_id}: '{user_message}'")
        now_str = datetime.now(timezone.utc).isoformat()

        # 1. Store user message in policy_chat_history.db
        with db_manager.get_chat_history_connection() as conn:
            conn.execute("""
                INSERT INTO chat_messages (ai_case_id, timestamp, sender, content, model_used)
                VALUES (?, ?, ?, ?, ?)
            """, (ai_case_id, now_str, "analyst", user_message, None))
            conn.commit()

        # 2. Retrieve past conversation history from DB
        history = self.get_chat_history(ai_case_id)
        history_context = "\n".join([f"{m['sender']}: {m['content']}" for m in history[-6:]])

        # 3. Retrieve relevant policy chunks
        policy_context = self._policy_chunks

        # 4. Construct prompt
        raw_prompt = (
            f"SYSTEM: You are the Bank OFD Policy Chat Agent (Gemini 2.5 Pro). "
            f"Answer the fraud analyst's question regarding case {ai_case_id}.\n"
            f"CASE SUMMARY CONTEXT:\n{case_summary or 'Active fraud investigation'}\n\n"
            f"APPLICABLE BANK SOP INSTRUCTIONS:\n{policy_context}\n\n"
            f"CONVERSATION HISTORY:\n{history_context}\n\n"
            f"ANALYST QUESTION: {user_message}\n"
            f"Provide an authoritative, clear explanation citing relevant SOP codes."
        )

        # 5. Mask PII before Tachyon LLM invocation
        masked_prompt, token_map = PIIMasker.mask_text(raw_prompt)

        # 6. Call LLM (gemini-2.5-pro via Tachyon pool)
        llm_response = await tachyon_pool.call_model(
            model_name="gemini-2.5-pro",
            prompt=masked_prompt,
            system_instructions="You are an enterprise banking fraud policy reasoning assistant."
        )

        # 7. Record to immutable audit store
        audit_store.record_event(
            case_id=ai_case_id,
            agent_name="Policy Chat Agent",
            action_type="POLICY_CHAT_QNA",
            payload_summary=f"Analyst asked: '{user_message[:50]}...'. Answered via {self.model}"
        )

        # 8. Store agent response in policy_chat_history.db
        resp_now_str = datetime.now(timezone.utc).isoformat()
        with db_manager.get_chat_history_connection() as conn:
            conn.execute("""
                INSERT INTO chat_messages (ai_case_id, timestamp, sender, content, model_used, masked_prompt)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (ai_case_id, resp_now_str, "policy_chat_agent", llm_response, self.model, masked_prompt[:200]))
            conn.commit()

        return {
            "ai_case_id": ai_case_id,
            "sender": "policy_chat_agent",
            "content": llm_response,
            "timestamp": resp_now_str,
            "model_used": self.model,
            "pii_masked": True
        }

    def get_chat_history(self, ai_case_id: str) -> List[Dict[str, Any]]:
        """Retrieves conversational history from policy_chat_history.db."""
        with db_manager.get_chat_history_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT message_id, timestamp, sender, content, model_used
                FROM chat_messages
                WHERE ai_case_id = ?
                ORDER BY message_id ASC
            """, (ai_case_id,))
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "timestamp": r[1],
                    "sender": r[2],
                    "content": r[3],
                    "model_used": r[4]
                }
                for r in rows
            ]
