from typing import Dict, Any
from fastapi import APIRouter, Request

router = APIRouter(prefix="/metrics", tags=["Metrics"])

@router.get("", response_model=Dict[str, Any])
async def get_system_metrics(request: Request):
    orchestrator = request.app.state.orchestrator
    metrics = orchestrator.db.get_metrics()
    return metrics
