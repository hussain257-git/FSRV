from fastapi import APIRouter, HTTPException, Request
from app.models.actions import AnalystActionRequest, AnalystActionResponse

router = APIRouter(prefix="/cases", tags=["Actions"])

@router.post("/{case_id}/actions", response_model=AnalystActionResponse)
async def take_analyst_action(
    case_id: str,
    action_req: AnalystActionRequest,
    request: Request
):
    """
    Step 12 in Architecture: OFD Case Analyst executes action based on
    recommendations (e.g. Block Account, Restrict Card, Escalate, Dismiss).
    """
    orchestrator = request.app.state.orchestrator
    try:
        response = await orchestrator.execute_analyst_action(
            case_id=case_id,
            action_request=action_req
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
