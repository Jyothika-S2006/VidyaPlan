"""API routes for plan creation, scenarios, stress-test, VOI, baselines, copilot, explanations, and memo PDF."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.db.models import PlanRun, Recommendation, School, FacilityEvidence

logger = logging.getLogger(__name__)
router = APIRouter()


class PlanRequest(BaseModel):
    budget: float = Field(..., gt=0)
    cohort_only: bool = True
    weight_overrides: Optional[dict] = None
    cost_overrides: Optional[dict] = None


async def _build_items(session: AsyncSession, cohort_only: bool, costs: dict, weights: dict):
    """Shared helper: build eligible, missing, and blocked item lists from DB."""
    q = select(School, FacilityEvidence).join(FacilityEvidence, FacilityEvidence.school_id == School.id)
    if cohort_only:
        q = q.where(School.in_cohort == True)
    result = await session.execute(q)
    rows = result.all()

    school_evidence: dict = {}
    school_map: dict = {}
    for school, ev in rows:
        school_map[school.id] = school
        if school.id not in school_evidence:
            school_evidence[school.id] = {}
        school_evidence[school.id][ev.facility] = ev.state

    eligible, missing, blocked = [], [], []
    for school_id, evidence in school_evidence.items():
        school = school_map[school_id]
        need_multiplier = 1.0
        for facility in ["electricity", "library", "computers"]:
            state = evidence.get(facility, "MISSING")
            cost = costs.get(facility, 200000)
            priority = weights.get(facility, 0.8) * need_multiplier
            item = {
                "id": f"{school_id}_{facility}",
                "school_id": school_id,
                "school_name": school.name,
                "district": school.district,
                "facility": facility,
                "cost": cost,
                "priority": priority,
                "electricity_state": evidence.get("electricity", "MISSING"),
            }
            if state == "CONFIRMED_GAP":
                if facility == "computers":
                    elec_state = evidence.get("electricity", "MISSING")
                    if elec_state in ("MISSING", "UNRELIABLE"):
                        item["reason_code"] = "BLOCKED_PREREQ_UNVERIFIED"
                        blocked.append(item)
                        continue
                eligible.append(item)
            elif state == "MISSING":
                missing.append(item)

    return eligible, missing, blocked, school_evidence, school_map


@router.post("/plan")
async def run_plan(req: PlanRequest, session: AsyncSession = Depends(get_session)):
    import yaml, os
    base = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config")
    with open(os.path.join(base, "costs.yaml")) as f:
        costs = yaml.safe_load(f)
    with open(os.path.join(base, "weights.yaml")) as f:
        weights = yaml.safe_load(f)
    if req.cost_overrides:
        costs.update(req.cost_overrides)
    if req.weight_overrides:
        weights.update(req.weight_overrides)

    from app.solver.model import solve
    eligible, missing, blocked, school_evidence, school_map = await _build_items(session, req.cohort_only, costs, weights)

    if not eligible:
        return {"plan_id": None, "budget": req.budget, "budget_used": 0, "budget_remaining": req.budget, "objective": 0, "selected": [], "deferred": [], "blocked": [], "kpis": {"interventions_funded": 0, "schools_improved": 0, "deferred_count": 0}}

    result_data = solve(eligible, req.budget)

    plan = PlanRun(budget=req.budget, objective=result_data["objective"], budget_used=result_data["budget_used"], params={"costs": costs, "weights": weights})
    session.add(plan)
    await session.flush()

    selected_recs: list[Recommendation] = []
    for item in result_data["selected"]:
        rec = Recommendation(plan_run_id=plan.id, school_id=item["school_id"], facility_type=item["facility"], cost=item["cost"], priority=item["priority"], status="selected")
        session.add(rec)
        selected_recs.append(rec)
    for item in result_data["deferred"]:
        session.add(Recommendation(plan_run_id=plan.id, school_id=item["school_id"], facility_type=item["facility"], cost=item["cost"], priority=item["priority"], status="deferred", reason_code=item.get("reason_code", "OUT_OF_BUDGET")))
    for item in blocked:
        session.add(Recommendation(plan_run_id=plan.id, school_id=item["school_id"], facility_type=item["facility"], cost=item["cost"], priority=item["priority"], status="deferred", reason_code="BLOCKED_PREREQ_UNVERIFIED"))
    await session.flush()  # assigns IDs to selected_recs before commit
    await session.commit()

    # Enrich selected items with their DB recommendation IDs for the review workflow
    selected_with_ids = [
        {**item, "id": rec.id}
        for item, rec in zip(result_data["selected"], selected_recs)
    ]

    # Build school list for orchestrator (evidence + eligibility bundled)
    schools_for_pipeline = [
        {
            "id": sid,
            "name": school_map[sid].name,
            "district": school_map[sid].district,
            "evidence": school_evidence[sid],
            "eligibility": {f: school_evidence[sid].get(f, "MISSING") for f in ["electricity", "library", "computers"]},
        }
        for sid in school_map
    ]
    import asyncio
    from app.agents.orchestrator import run_pipeline

    # Run the agent pipeline in a thread so it doesn't block the HTTP response.
    # The trace is collected synchronously there but we fire-and-forget here;
    # the client fetches /api/plan/{id}/trace once the plan page loads.
    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        None,
        lambda: run_pipeline(
            plan_id=plan.id,
            schools=schools_for_pipeline,
            selected=selected_with_ids,
            deferred=result_data["deferred"],
            budget=req.budget,
            budget_used=result_data["budget_used"],
        ),
    )

    schools_improved = len({i["school_id"] for i in result_data["selected"]})
    return {
        "plan_id": plan.id, "budget": req.budget, "budget_used": result_data["budget_used"],
        "budget_remaining": req.budget - result_data["budget_used"], "objective": result_data["objective"],
        "selected": selected_with_ids, "deferred": result_data["deferred"],
        "blocked": [{"school_name": b["school_name"], "facility": b["facility"], "reason_code": "BLOCKED_PREREQ_UNVERIFIED"} for b in blocked],
        "kpis": {"interventions_funded": len(result_data["selected"]), "schools_improved": schools_improved, "deferred_count": len(result_data["deferred"])},
    }


@router.get("/plan/{plan_id}")
async def get_plan(plan_id: int, session: AsyncSession = Depends(get_session)):
    plan = await session.get(PlanRun, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    result = await session.execute(select(Recommendation, School).join(School, School.id == Recommendation.school_id).where(Recommendation.plan_run_id == plan_id))
    recs = [{"id": rec.id, "school_id": rec.school_id, "school_name": school.name, "facility_type": rec.facility_type, "cost": rec.cost, "priority": rec.priority, "status": rec.status, "reason_code": rec.reason_code, "robustness": rec.robustness, "review_status": rec.review_status, "explanation": rec.explanation, "explanation_source": rec.explanation_source} for rec, school in result.all()]
    return {"id": plan.id, "budget": plan.budget, "budget_used": plan.budget_used, "objective": plan.objective, "status": plan.status, "created_at": plan.created_at.isoformat(), "recommendations": recs}


@router.get("/plans")
async def list_plans(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(PlanRun).order_by(PlanRun.created_at.desc()).limit(20))
    return [{"id": p.id, "budget": p.budget, "budget_used": p.budget_used, "objective": p.objective, "status": p.status, "created_at": p.created_at.isoformat()} for p in result.scalars().all()]


class StressRequest(BaseModel):
    budget: float = Field(..., gt=0)
    cohort_only: bool = True
    n_scenarios: int = Field(default=100, ge=10, le=500)
    seed: int = 42


@router.post("/plan/stress")
async def run_stress(req: StressRequest, session: AsyncSession = Depends(get_session)):
    import yaml, os
    base = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config")
    with open(os.path.join(base, "costs.yaml")) as f:
        costs = yaml.safe_load(f)
    with open(os.path.join(base, "weights.yaml")) as f:
        weights = yaml.safe_load(f)

    from app.solver.model import solve
    from app.solver.stress import estimate_p_gap, run_stress_test

    eligible, missing, blocked, school_evidence, school_map = await _build_items(session, req.cohort_only, costs, weights)
    if not eligible:
        raise HTTPException(status_code=400, detail="No eligible items found")

    base_result = solve(eligible, req.budget)
    base_ids = {i["id"] for i in base_result["selected"]}

    # Build all_evidence for P(gap) estimation
    all_ev_result = await session.execute(select(FacilityEvidence, School).join(School, School.id == FacilityEvidence.school_id))
    all_evidence = [{"school_id": ev.school_id, "district": school.district, "facility": ev.facility, "state": ev.state} for ev, school in all_ev_result.all()]

    # Estimate P(gap) for missing items
    p_gap: dict = {}
    for facility in ["electricity", "library", "computers"]:
        missing_for_fac = [m for m in missing if m["facility"] == facility]
        p = estimate_p_gap(missing_for_fac, all_evidence, facility)
        p_gap.update(p)

    stress_result = run_stress_test(
        base_selected_ids=base_ids,
        base_objective=base_result["objective"],
        eligible_items=eligible,
        missing_items=missing,
        p_gap=p_gap,
        budget=req.budget,
        n_scenarios=req.n_scenarios,
        seed=req.seed,
    )

    return {
        "budget": req.budget,
        "n_scenarios": stress_result.n_scenarios,
        "seed": stress_result.seed,
        "base_objective": stress_result.base_objective,
        "expected_regret_rs": stress_result.expected_regret_rs,
        "expected_regret_pct": stress_result.expected_regret_pct,
        "details": stress_result.details,
        "provenance": "SIMULATED",
    }


@router.get("/plan/{plan_id}/verify-first")
async def verify_first(plan_id: int, session: AsyncSession = Depends(get_session)):
    plan = await session.get(PlanRun, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    import yaml, os
    base = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config")
    with open(os.path.join(base, "costs.yaml")) as f:
        costs = yaml.safe_load(f)
    with open(os.path.join(base, "weights.yaml")) as f:
        weights = yaml.safe_load(f)

    from app.solver.model import solve
    from app.solver.stress import estimate_p_gap
    from app.solver.voi import compute_voi

    eligible, missing, blocked, _, school_map = await _build_items(session, True, costs, weights)
    base_result = solve(eligible, plan.budget)

    all_ev_result = await session.execute(select(FacilityEvidence, School).join(School, School.id == FacilityEvidence.school_id))
    all_evidence = [{"school_id": ev.school_id, "district": school.district, "facility": ev.facility, "state": ev.state} for ev, school in all_ev_result.all()]

    p_gap: dict = {}
    for facility in ["electricity", "library", "computers"]:
        missing_for_fac = [m for m in missing if m["facility"] == facility]
        p = estimate_p_gap(missing_for_fac, all_evidence, facility)
        p_gap.update(p)

    entries = compute_voi(eligible, missing, blocked, p_gap, plan.budget, base_result["objective"])
    return [{"school_id": e.school_id, "school_name": e.school_name, "facility": e.facility, "district": e.district, "p_gap": e.p_gap, "voi_rs": e.voi_rs, "action_text": e.action_text, "provenance": "SIMULATED"} for e in entries]


class CompareRequest(BaseModel):
    budget: float = Field(..., gt=0)
    cohort_only: bool = True


@router.post("/plan/compare")
async def compare_plan(req: CompareRequest, session: AsyncSession = Depends(get_session)):
    import yaml, os
    base = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config")
    with open(os.path.join(base, "costs.yaml")) as f:
        costs = yaml.safe_load(f)
    with open(os.path.join(base, "weights.yaml")) as f:
        weights = yaml.safe_load(f)

    from app.solver.scenarios import compare_scenarios, marginal_view
    eligible, missing, blocked, _, _ = await _build_items(session, req.cohort_only, costs, weights)

    cmp = compare_scenarios(eligible, req.budget)
    marginal = marginal_view(eligible, req.budget)

    return {
        "base": {"budget": cmp.base.budget, "budget_used": cmp.base.budget_used, "funded": cmp.base.interventions_funded, "schools": cmp.base.schools_improved, "objective": cmp.base.objective},
        "low": {"budget": cmp.low.budget, "budget_used": cmp.low.budget_used, "funded": cmp.low.interventions_funded, "schools": cmp.low.schools_improved, "objective": cmp.low.objective},
        "high": {"budget": cmp.high.budget, "budget_used": cmp.high.budget_used, "funded": cmp.high.interventions_funded, "schools": cmp.high.schools_improved, "objective": cmp.high.objective},
        "gained_in_high": [{"school_name": i["school_name"], "facility": i["facility"]} for i in cmp.gained_in_high],
        "lost_in_low": [{"school_name": i["school_name"], "facility": i["facility"]} for i in cmp.lost_in_low],
        "marginal": {"extra_budget": marginal.extra_budget, "new_items": [{"school_name": i["school_name"], "facility": i["facility"]} for i in marginal.new_items], "delta_interventions": marginal.delta_interventions},
        "provenance": "SIMULATED",
    }


@router.get("/plan/{plan_id}/baselines")
async def get_baselines(plan_id: int, session: AsyncSession = Depends(get_session)):
    plan = await session.get(PlanRun, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    import yaml, os
    base = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config")
    with open(os.path.join(base, "costs.yaml")) as f:
        costs = yaml.safe_load(f)
    with open(os.path.join(base, "weights.yaml")) as f:
        weights = yaml.safe_load(f)

    from app.solver.model import solve
    from app.solver.baselines import run_baselines
    eligible, _, _, _, _ = await _build_items(session, True, costs, weights)
    opt = solve(eligible, plan.budget)
    results = run_baselines(eligible, plan.budget, opt, n_random=100, seed=42)
    return [{"method": r.method, "objective": r.objective, "interventions_funded": r.interventions_funded, "schools_improved": r.schools_improved, "budget_used": r.budget_used, "pct_vs_optimiser": r.pct_vs_optimiser, "provenance": "SIMULATED"} for r in results]


@router.get("/plan/{plan_id}/trace")
async def get_plan_trace(plan_id: int, session: AsyncSession = Depends(get_session)):
    """Return agent pipeline trace steps for a plan (may be empty if still running)."""
    from app.db.models import AgentTrace
    result = await session.execute(
        select(AgentTrace).where(AgentTrace.plan_run_id == plan_id).order_by(AgentTrace.id)
    )
    steps = result.scalars().all()
    return [
        {
            "agent": s.agent,
            "tool_called": s.tool_called,
            "latency_ms": s.latency_ms,
            "source": s.source,
            "output_summary": s.output_summary,
        }
        for s in steps
    ]


@router.get("/plan/{plan_id}/explanations")
async def get_explanations(plan_id: int, session: AsyncSession = Depends(get_session)):
    plan = await session.get(PlanRun, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    result = await session.execute(select(Recommendation, School).join(School, School.id == Recommendation.school_id).where(Recommendation.plan_run_id == plan_id))
    items = [{"school_id": rec.school_id, "school_name": school.name, "facility": rec.facility_type, "cost": rec.cost, "priority": rec.priority, "status": rec.status, "reason_code": rec.reason_code} for rec, school in result.all()]
    selected = [i for i in items if i["status"] == "selected"]
    deferred = [i for i in items if i["status"] == "deferred"]
    from app.agents.tradeoff_agent import generate_batch_rationales
    rationales = generate_batch_rationales(selected, deferred, plan.budget_used, plan.budget)
    return {"plan_id": plan_id, "rationales": rationales, "provenance": "SIMULATED"}


class CopilotRequest(BaseModel):
    instruction: str
    budget: float = Field(..., gt=0)
    cohort_only: bool = True


@router.post("/copilot")
async def copilot(req: CopilotRequest, session: AsyncSession = Depends(get_session)):
    import yaml, os
    base = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config")
    with open(os.path.join(base, "costs.yaml")) as f:
        costs = yaml.safe_load(f)
    with open(os.path.join(base, "weights.yaml")) as f:
        weights = yaml.safe_load(f)

    from app.agents.portfolio_agent import run_copilot
    eligible, _, _, _, _ = await _build_items(session, req.cohort_only, costs, weights)
    return await run_copilot(req.instruction, eligible, req.budget)


@router.get("/plan/{plan_id}/memo.pdf")
async def get_memo(plan_id: int, session: AsyncSession = Depends(get_session)):
    plan = await session.get(PlanRun, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    import yaml, os
    base = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config")
    with open(os.path.join(base, "costs.yaml")) as f:
        costs = yaml.safe_load(f)
    with open(os.path.join(base, "weights.yaml")) as f:
        weights = yaml.safe_load(f)

    result = await session.execute(select(Recommendation, School).join(School, School.id == Recommendation.school_id).where(Recommendation.plan_run_id == plan_id))
    recs = [{"school_name": school.name, "facility_type": rec.facility_type, "cost": rec.cost, "status": rec.status, "reason_code": rec.reason_code, "review_status": rec.review_status} for rec, school in result.all()]

    plan_dict = {"id": plan.id, "budget": plan.budget, "budget_used": plan.budget_used, "objective": plan.objective, "status": plan.status, "created_at": plan.created_at.isoformat()}

    from app.export.memo_pdf import generate_memo_pdf
    pdf_bytes = generate_memo_pdf(plan_dict, recs, costs, weights, is_final=(plan.status == "final"))
    if not pdf_bytes:
        raise HTTPException(status_code=500, detail="PDF generation failed. Ensure reportlab is installed.")

    filename = f"vidyaplan_memo_plan{plan_id}{'_final' if plan.status == 'final' else '_draft'}.pdf"
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})
