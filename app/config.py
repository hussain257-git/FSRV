import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
WEB_DIR = BASE_DIR / "web"
DB_FILE = BASE_DIR / "cases.db"

APP_NAME = "Bank Fraud Investigation Assist (Multi-Agent Orchestration)"
VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
TARGET_SLA_SECONDS = 3.0
