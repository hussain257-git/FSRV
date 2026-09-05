import pytest
import os
import sqlite3
from app.masking import PIIMasker
from app.tachyon_client_pool import tachyon_pool
from app.audit_store import audit_store
from app.db import db_manager
from app.agents.policy_chat import PolicyChatAgent
from fastapi.testclient import TestClient
from app.main import app

def test_pii_masking():
    raw_text = (
        "Customer John Doe SSN 123-45-6789 with PAN 4532-1189-9941-2041 "
        "and email jdoe@enterprise.com phoned +1-312-555-0199 about account ACT-8841-9921."
    )
    masked, token_map = PIIMasker.mask_text(raw_text)
    
    # Verify sensitive data is removed
    assert "123-45-6789" not in masked
    assert "4532-1189-9941-2041" not in masked
    assert "jdoe@enterprise.com" not in masked
    assert "+1-312-555-0199" not in masked
    assert "ACT-8841-9921" not in masked
    
    # Verify redaction tokens exist
    assert "***-**-" in masked
    assert "-****-****-" in masked
    assert "@enterprise.com" in masked
    assert "+1-***-***-" in masked
    assert "ACT-****-" in masked
    assert len(token_map) >= 5

@pytest.mark.asyncio
async def test_tachyon_client_pool():
    # Test gpt5.1 routing
    resp_gpt = await tachyon_pool.call_model(
        model_name="gpt5.1",
        prompt="Evaluate policy risk",
        system_instructions="Bank OFD Decision Engine"
    )
    assert isinstance(resp_gpt, str)
    assert len(resp_gpt) > 0

    # Test gemini-2.5-pro routing
    resp_gemini = await tachyon_pool.call_model(
        model_name="gemini-2.5-pro",
        prompt="What is SOP-SEC-802?",
        system_instructions="Bank OFD Chat"
    )
    assert isinstance(resp_gemini, str)
    assert len(resp_gemini) > 0

def test_audit_store_hash_chain():
    # Verify hash chaining
    e1 = audit_store.record_event("TEST-CHAIN-01", "AgentA", "ACTION_1", "Payload 1")
    e2 = audit_store.record_event("TEST-CHAIN-01", "AgentB", "ACTION_2", "Payload 2")
    
    assert e2["prev_hash"] == e1["record_hash"]
    
    # Verify chain integrity check
    chain_valid = audit_store.verify_chain("TEST-CHAIN-01")
    assert chain_valid is True

def test_enterprise_multi_db():
    # Verify chat history db
    with db_manager.get_chat_history_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_messages'")
        assert cursor.fetchone() is not None

    # Verify case context db
    with db_manager.get_context_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='case_context'")
        assert cursor.fetchone() is not None

    # Verify sop actions db
    with db_manager.get_sop_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sop_actions'")
        assert cursor.fetchone() is not None

import uuid

@pytest.mark.asyncio
async def test_policy_chat_agent():
    agent = PolicyChatAgent()
    case_id = f"TEST-CHAT-{uuid.uuid4().hex[:8]}"
    
    # Send first question
    res1 = await agent.chat(
        ai_case_id=case_id,
        user_message="Should I freeze the account for high value wire from Lagos?",
        case_summary="High confidence account takeover"
    )
    assert res1["ai_case_id"] == case_id
    assert res1["sender"] == "policy_chat_agent"
    assert "SOP-SEC-802" in res1["content"] or "BLOCK_ACCOUNT" in res1["content"]

    # Verify history is stored
    history = agent.get_chat_history(case_id)
    assert len(history) == 2  # analyst + agent
    assert history[0]["sender"] == "analyst"
    assert history[1]["sender"] == "policy_chat_agent"

def test_chat_api_endpoints():
    client = TestClient(app)
    
    # Post chat message
    post_res = client.post("/api/chat", json={
        "ai_case_id": "CASE-ATO-8921",
        "message": "What is the primary action recommended?"
    })
    assert post_res.status_code == 200
    data = post_res.json()
    assert data["ai_case_id"] == "CASE-ATO-8921"
    assert data["sender"] == "policy_chat_agent"
    assert len(data["content"]) > 10

    # Get history
    hist_res = client.get("/api/chat/CASE-ATO-8921/history")
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert isinstance(hist, list)
    assert len(hist) >= 2
