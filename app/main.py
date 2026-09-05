import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import APP_NAME, VERSION, WEB_DIR
from app.database import CaseDatabase
from app.agents.orchestrator import CaseOrchestratorAgent
from app.models.alert import FraudAlert, CustomerProfile
from app.api import cases_router, actions_router, metrics_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("app.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB and Orchestrator
    logger.info("Initializing Bank Fraud Investigation Assist Engine...")
    db = CaseDatabase()
    orchestrator = CaseOrchestratorAgent(db)
    app.state.orchestrator = orchestrator

    # Pre-orchestrate seed scenarios into Case DB for immediate demo readiness
    logger.info("Pre-orchestrating seed cases into Case DB...")
    for sc in db.get_seed_data():
        try:
            alert = FraudAlert(**sc["alert"])
            customer = CustomerProfile(**sc["customer"])
            await orchestrator.handle_fraud_alert(
                alert=alert,
                customer=customer,
                raw_history=sc.get("raw_history", []),
                raw_notes=sc.get("raw_notes", [])
            )
        except Exception as e:
            logger.error(f"Failed to orchestrate initial seed case: {e}")

    logger.info("Bank Fraud Investigation Assist initialized and ready.")
    yield
    logger.info("Shutting down Bank Fraud Investigation Assist Engine.")

app = FastAPI(
    title=APP_NAME,
    version=VERSION,
    description="Multi-Agent Orchestration prototype for Bank Fraud Case Assist",
    lifespan=lifespan
)

# Ensure app.state.orchestrator is always available immediately
_default_db = CaseDatabase()
_default_orchestrator = CaseOrchestratorAgent(_default_db)
app.state.orchestrator = _default_orchestrator

# Enable CORS for all origins in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import cases_router, actions_router, metrics_router, chat_router

# API Routers
app.include_router(cases_router, prefix="/api")
app.include_router(actions_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(chat_router, prefix="/api")

# Static files for PREVENT UI
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

@app.get("/")
async def serve_ui_root():
    index_path = WEB_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": f"{APP_NAME} API active. Access /docs for Swagger UI."}
