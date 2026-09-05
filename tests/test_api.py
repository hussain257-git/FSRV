import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_api_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Pre-populate cases
        reset_res = await ac.post("/api/cases/reset-all")
        assert reset_res.status_code == 200

        # 1. Test case list endpoint
        res = await ac.get("/api/cases")
        assert res.status_code == 200
        cases = res.json()
        assert len(cases) >= 1

        first_case_id = cases[0]["case_id"]

        # 2. Test get single case
        res_single = await ac.get(f"/api/cases/{first_case_id}")
        assert res_single.status_code == 200
        case_data = res_single.json()
        assert case_data["case_id"] == first_case_id
        assert "consolidated_summary" in case_data
        assert "policy_result" in case_data

        # 3. Test pull next case
        res_next = await ac.get("/api/cases/next")
        assert res_next.status_code == 200
        assert "case_id" in res_next.json()

        # 4. Test analyst action execution (e.g. Block Account)
        action_payload = {
            "action_type": "BLOCK_ACCOUNT",
            "analyst_id": "OFD-TEST-001",
            "analyst_name": "Test Analyst",
            "investigator_notes": "Test freezing account per SOP-SEC-802"
        }
        res_act = await ac.post(f"/api/cases/{first_case_id}/actions", json=action_payload)
        assert res_act.status_code == 200
        action_resp = res_act.json()
        assert action_resp["status"] == "RESOLVED_BLOCKED"

        # 5. Test metrics endpoint
        res_metrics = await ac.get("/api/metrics")
        assert res_metrics.status_code == 200
        metrics = res_metrics.json()
        assert "total_cases" in metrics
        assert "sla_target_met_percent" in metrics
