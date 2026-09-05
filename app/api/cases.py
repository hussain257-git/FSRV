from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from app.models.case import CaseRecord
from app.models.alert import FraudAlert, CustomerProfile

router = APIRouter(prefix="/cases", tags=["Cases"])

class SimulateAlertRequest(BaseModel):
    scenario_index: Optional[int] = None  # 0 to 3 for seed cases
    custom_alert: Optional[FraudAlert] = None
    custom_customer: Optional[CustomerProfile] = None

@router.get("", response_model=List[CaseRecord])
async def list_cases(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by case status")
):
    orchestrator = request.app.state.orchestrator
    return orchestrator.db.list_cases(status=status)

@router.get("/next", response_model=CaseRecord)
async def pull_next_case(request: Request):
    """
    Step 10 & 11 in Architecture: OFD Case Analyst pulls next pending case.
    """
    orchestrator = request.app.state.orchestrator
    case = orchestrator.db.get_next_unreviewed_case()
    if not case:
        # If none unreviewed, return any case
        all_cases = orchestrator.db.list_cases()
        if all_cases:
            return all_cases[0]
        raise HTTPException(status_code=404, detail="No cases currently available in queue.")
    return case

@router.get("/{case_id}", response_model=CaseRecord)
async def get_case(case_id: str, request: Request):
    orchestrator = request.app.state.orchestrator
    case = orchestrator.db.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")
    return case

@router.post("/simulate", response_model=CaseRecord)
async def simulate_alert(request: Request, sim_req: SimulateAlertRequest):
    """
    Step 1 -> 9: Ingests an alert, creates case, triggers multi-agent orchestration,
    persists consolidated summary, and returns the case.
    """
    orchestrator = request.app.state.orchestrator
    seed_scenarios = orchestrator.db.get_seed_data()

    if sim_req.scenario_index is not None and 0 <= sim_req.scenario_index < len(seed_scenarios):
        sc = seed_scenarios[sim_req.scenario_index]
        alert = FraudAlert(**sc["alert"])
        customer = CustomerProfile(**sc["customer"])
        raw_hist = sc.get("raw_history", [])
        raw_notes = sc.get("raw_notes", [])
    elif sim_req.custom_alert and sim_req.custom_customer:
        alert = sim_req.custom_alert
        customer = sim_req.custom_customer
        raw_hist = []
        raw_notes = []
    else:
        # Default to first seed scenario (ATO)
        sc = seed_scenarios[0]
        alert = FraudAlert(**sc["alert"])
        customer = CustomerProfile(**sc["customer"])
        raw_hist = sc.get("raw_history", [])
        raw_notes = sc.get("raw_notes", [])

    case = await orchestrator.handle_fraud_alert(
        alert=alert,
        customer=customer,
        raw_history=raw_hist,
        raw_notes=raw_notes
    )
    return case

@router.post("/reset-all", response_model=Dict[str, Any])
async def reset_all_cases(request: Request):
    """
    Orchestrates all seed scenarios fresh into the database.
    """
    orchestrator = request.app.state.orchestrator
    seed_scenarios = orchestrator.db.get_seed_data()
    orchestrated_cases = []

    for sc in seed_scenarios:
        alert = FraudAlert(**sc["alert"])
        customer = CustomerProfile(**sc["customer"])
        case = await orchestrator.handle_fraud_alert(
            alert=alert,
            customer=customer,
            raw_history=sc.get("raw_history", []),
            raw_notes=sc.get("raw_notes", [])
        )
        orchestrated_cases.append(case.case_id)

    return {
        "status": "success",
        "message": f"Successfully re-orchestrated {len(orchestrated_cases)} scenarios.",
        "case_ids": orchestrated_cases
    }
