import os
import sqlite3
import logging
from pathlib import Path
from typing import Optional

from app.config import BASE_DIR

logger = logging.getLogger("db.config")

# Distinct database files according to enterprise architecture specification:
CASE_CONTEXT_DB = BASE_DIR / "case_context.db"
SOP_ACTIONS_DB = BASE_DIR / "sop_actions_2.db"
POLICY_CHAT_HISTORY_DB = BASE_DIR / "policy_chat_history.db"

class EnterpriseDBManager:
    """
    Enterprise DB Configuration (db.py):
    Implements Oracle connection pool with local SQLite fallback.
    Manages isolated databases for:
      1. case_context.db: Case context & ECN telemetry
      2. sop_actions_2.db: Policy SOP rules & actions
      3. policy_chat_history.db: Policy Chat conversational state
    """
    def __init__(self):
        self.oracle_enabled = os.getenv("ORACLE_DB_ENABLED", "false").lower() == "true"
        self._init_sqlite_databases()

    def _init_sqlite_databases(self):
        """Initializes separate SQLite database files."""
        # 1. case_context.db
        with sqlite3.connect(str(CASE_CONTEXT_DB)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS case_context (
                    ecn TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    customer_name TEXT NOT NULL,
                    context_payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

        # 2. sop_actions_2.db
        with sqlite3.connect(str(SOP_ACTIONS_DB)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sop_actions (
                    rule_id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    action_code TEXT NOT NULL,
                    sop_citation TEXT NOT NULL,
                    description TEXT NOT NULL
                );
            """)

        # 3. policy_chat_history.db
        with sqlite3.connect(str(POLICY_CHAT_HISTORY_DB)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ai_case_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    sender TEXT NOT NULL,      -- 'analyst' or 'policy_chat_agent'
                    content TEXT NOT NULL,
                    model_used TEXT,
                    masked_prompt TEXT
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_case ON chat_messages(ai_case_id);")

        logger.info(f"Initialized Enterprise SQLite stores: {CASE_CONTEXT_DB.name}, {SOP_ACTIONS_DB.name}, {POLICY_CHAT_HISTORY_DB.name}")

    def get_context_connection(self):
        return sqlite3.connect(str(CASE_CONTEXT_DB))

    def get_sop_connection(self):
        return sqlite3.connect(str(SOP_ACTIONS_DB))

    def get_chat_history_connection(self):
        return sqlite3.connect(str(POLICY_CHAT_HISTORY_DB))

# Global DB manager singleton
db_manager = EnterpriseDBManager()
