import json
import hashlib
import sqlite3
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.config import DB_FILE

logger = logging.getLogger("audit.store")

class AuditStore:
    """
    Audit Store (audit_store.py in Enterprise Architecture):
    Maintains an append-only, tamper-evident immutable request/response
    trail for all multi-agent inferences and analyst actions, including
    cryptographic SHA-256 hash chaining.
    """
    def __init__(self, db_path = None):
        self.db_path = db_path or DB_FILE
        self._init_table()

    def _init_table(self):
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_trail_immutable (
                    sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    payload_summary TEXT NOT NULL,
                    prev_hash TEXT,
                    record_hash TEXT NOT NULL
                );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_imm_case ON audit_trail_immutable(case_id);")
            conn.commit()

    def _get_last_hash(self) -> str:
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT record_hash FROM audit_trail_immutable ORDER BY sequence_id DESC LIMIT 1")
            row = cursor.fetchone()
            return row[0] if row else "GENESIS_HASH_0000000000000000"

    def record_event(
        self,
        case_id: str,
        agent_name: str,
        action_type: str,
        payload_summary: str
    ) -> str:
        timestamp = datetime.now(timezone.utc).isoformat()
        prev_hash = self._get_last_hash()

        # Compute hash block
        hasher = hashlib.sha256()
        hasher.update(f"{case_id}:{timestamp}:{agent_name}:{action_type}:{payload_summary}:{prev_hash}".encode('utf-8'))
        record_hash = hasher.hexdigest()

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_trail_immutable (
                    case_id, timestamp, agent_name, action_type, payload_summary, prev_hash, record_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (case_id, timestamp, agent_name, action_type, payload_summary, prev_hash, record_hash))
            conn.commit()

        logger.info(f"[AuditStore] Recorded {action_type} by {agent_name} for case {case_id} [Hash: {record_hash[:8]}...]")
        return {
            "case_id": case_id,
            "timestamp": timestamp,
            "agent_name": agent_name,
            "action_type": action_type,
            "payload_summary": payload_summary,
            "prev_hash": prev_hash,
            "record_hash": record_hash
        }

    def verify_chain(self, case_id: str) -> bool:
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT case_id, timestamp, agent_name, action_type, payload_summary, prev_hash, record_hash
                FROM audit_trail_immutable
                WHERE case_id = ?
                ORDER BY sequence_id ASC
            """, (case_id,))
            rows = cursor.fetchall()
            for r in rows:
                c_id, ts, agent, action, summary, prev_h, rec_h = r
                hasher = hashlib.sha256()
                hasher.update(f"{c_id}:{ts}:{agent}:{action}:{summary}:{prev_h}".encode('utf-8'))
                if hasher.hexdigest() != rec_h:
                    return False
            return True

    def get_events(self, case_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sequence_id, case_id, timestamp, agent_name, action_type, payload_summary, record_hash
                FROM audit_trail_immutable
                WHERE case_id = ?
                ORDER BY sequence_id ASC
            """, (case_id,))
            rows = cursor.fetchall()
            return [
                {
                    "seq": r[0],
                    "case_id": r[1],
                    "timestamp": r[2],
                    "agent": r[3],
                    "action": r[4],
                    "details": r[5],
                    "hash": r[6]
                }
                for r in rows
            ]

# Global audit store instance
audit_store = AuditStore()
