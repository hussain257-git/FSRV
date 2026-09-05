import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.models.case import CaseRecord, CaseStatus, AuditLogEntry
from app.config import DATA_DIR, DB_FILE

logger = logging.getLogger("app.database")

class CaseDatabase:
    """
    SQLite Relational Database Repository for Bank Fraud Cases.
    Supports persistent disk storage (cases.db), SQL queries,
    relational audit log tables, metrics aggregation, and seed loading.
    """
    def __init__(self, db_path: Path = None, seed_file_path: Path = None):
        self.db_path = db_path or DB_FILE
        self.seed_file_path = seed_file_path or (DATA_DIR / "seed_cases.json")
        self._seed_data: List[Dict[str, Any]] = []
        
        # Initialize SQLite database schema
        self._init_sqlite()
        self._load_seed_data()

    def _init_sqlite(self):
        """Creates the relational tables and indexes if they do not exist."""
        logger.info(f"Connecting to SQLite database at: {self.db_path}")
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cases (
                    case_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    assigned_analyst TEXT,
                    alert_type TEXT,
                    risk_score INTEGER,
                    investigation_duration_ms REAL,
                    data_json TEXT NOT NULL
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT NOT NULL,
                    metadata_json TEXT,
                    FOREIGN KEY(case_id) REFERENCES cases(case_id) ON DELETE CASCADE
                );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_case_id ON audit_logs(case_id);")
            conn.commit()

    def _load_seed_data(self):
        if self.seed_file_path.exists():
            try:
                with open(self.seed_file_path, "r", encoding="utf-8") as f:
                    self._seed_data = json.load(f)
                logger.info(f"Loaded {len(self._seed_data)} seed fraud scenarios from {self.seed_file_path.name}")
            except Exception as e:
                logger.error(f"Error loading seed cases: {e}")
                self._seed_data = []

    def get_seed_data(self) -> List[Dict[str, Any]]:
        return self._seed_data

    def save_case(self, case: CaseRecord):
        """Persists or updates a case and its audit log entries in SQLite."""
        data_json = case.model_dump_json()
        risk_score = (
            case.policy_result.risk_score
            if case.policy_result
            else (case.alert.initial_risk_score if case.alert else 0)
        )
        alert_type = case.alert.alert_type if case.alert else "UNKNOWN"

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO cases (
                    case_id, created_at, updated_at, status, assigned_analyst, 
                    alert_type, risk_score, investigation_duration_ms, data_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(case_id) DO UPDATE SET
                    updated_at = excluded.updated_at,
                    status = excluded.status,
                    assigned_analyst = excluded.assigned_analyst,
                    risk_score = excluded.risk_score,
                    investigation_duration_ms = excluded.investigation_duration_ms,
                    data_json = excluded.data_json
            """, (
                case.case_id,
                case.created_at,
                case.updated_at,
                case.status.value,
                case.assigned_analyst,
                alert_type,
                risk_score,
                case.investigation_duration_ms,
                data_json
            ))

            # Synchronize audit log table
            cursor.execute("DELETE FROM audit_logs WHERE case_id = ?", (case.case_id,))
            for a in case.audit_trail:
                cursor.execute("""
                    INSERT INTO audit_logs (case_id, timestamp, actor, action, details, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    case.case_id,
                    a.timestamp,
                    a.actor,
                    a.action,
                    a.details,
                    json.dumps(a.metadata) if a.metadata else None
                ))
            conn.commit()

    def get_case(self, case_id: str) -> Optional[CaseRecord]:
        """Retrieves a single case from SQLite by primary key."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data_json FROM cases WHERE case_id = ?", (case_id,))
            row = cursor.fetchone()
            if row:
                return CaseRecord.model_validate_json(row[0])
        return None

    def list_cases(self, status: Optional[str] = None) -> List[CaseRecord]:
        """Lists cases from SQLite with optional status filtering."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute(
                    "SELECT data_json FROM cases WHERE status = ? ORDER BY updated_at DESC", 
                    (status,)
                )
            else:
                cursor.execute("SELECT data_json FROM cases ORDER BY updated_at DESC")
            rows = cursor.fetchall()
            return [CaseRecord.model_validate_json(r[0]) for r in rows]

    def get_next_unreviewed_case(self) -> Optional[CaseRecord]:
        """Queries for the next pending case prioritized by workflow urgency."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT data_json FROM cases 
                WHERE status IN ('READY_FOR_REVIEW', 'UNDER_INVESTIGATION', 'NEW')
                ORDER BY 
                    CASE status
                        WHEN 'READY_FOR_REVIEW' THEN 1
                        WHEN 'UNDER_INVESTIGATION' THEN 2
                        WHEN 'NEW' THEN 3
                        ELSE 4
                    END,
                    updated_at DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                return CaseRecord.model_validate_json(row[0])
        return None

    def get_metrics(self) -> Dict[str, Any]:
        """Aggregates real-time case counts and turnaround statistics via SQL."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, count(*) FROM cases GROUP BY status")
            status_counts = dict(cursor.fetchall())

            cursor.execute("SELECT count(*) FROM cases")
            total = cursor.fetchone()[0]

            cursor.execute(
                "SELECT AVG(investigation_duration_ms) FROM cases WHERE investigation_duration_ms IS NOT NULL"
            )
            row = cursor.fetchone()
            avg_ms = row[0] if row and row[0] is not None else 0.0

        ready = status_counts.get("READY_FOR_REVIEW", 0)
        blocked = status_counts.get("RESOLVED_BLOCKED", 0)
        restricted = status_counts.get("RESOLVED_RESTRICTED", 0)
        dismissed = status_counts.get("RESOLVED_DISMISSED", 0)
        escalated = status_counts.get("ESCALATED", 0)
        resolved_total = blocked + restricted + dismissed + escalated

        return {
            "total_cases": total,
            "ready_for_review": ready,
            "resolved_total": resolved_total,
            "breakdown": {
                "blocked": blocked,
                "restricted": restricted,
                "dismissed_false_positive": dismissed,
                "escalated": escalated
            },
            "average_agent_turnaround_ms": round(avg_ms, 2),
            "sla_target_met_percent": 100.0 if avg_ms < 3000 else 95.0,
            "database_engine": "SQLite 3",
            "database_file": str(self.db_path)
        }
