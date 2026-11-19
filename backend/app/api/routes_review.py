"""API routes for human review of recommendations."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.db.models import Recommendation, Review, PlanRun, AuditLog

logger = logging.getLogger(__name__)
router = APIRouter()


class ReviewRequest(BaseModel):
    """Request body for submitting a review decision."""
    decision: str  # approved, rejected
    note: Optional[str] = None
    reviewer: str


@router.post("/reviews/{recommendation_id}")
async def submit_review(
    recommendation_id: int,
    req: ReviewRequest,
    session: AsyncSession = Depends(get_session),
):
    """Approve or reject a recommendation."""
    if req.decision not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'rejected'")

    rec = await session.get(Recommendation, recommendation_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    before = {"review_status": rec.review_status}
    rec.review_status = req.decision

    review = Review(
        recommendation_id=recommendation_id,
        decision=req.decision,
        note=req.note,
        reviewer=req.reviewer,
    )
    session.add(review)

    audit = AuditLog(
        actor=req.reviewer,
        action="review",
        entity="recommendation",
        entity_id=recommendation_id,
        before_state=before,
        after_state={"review_status": req.decision},
    )
    session.add(audit)
    await session.commit()
    return {"status": "ok", "recommendation_id": recommendation_id, "decision": req.decision}


@router.post("/plan/{plan_id}/finalize")
async def finalize_plan(
    plan_id: int,
    reviewer: str,
    session: AsyncSession = Depends(get_session),
):
    """Move plan from in_review to final if all recommendations are reviewed."""
    plan = await session.get(PlanRun, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    result = await session.execute(
        select(Recommendation).where(
            Recommendation.plan_run_id == plan_id,
            Recommendation.status == "selected",
            Recommendation.review_status == "pending",
        )
    )
    pending = result.scalars().all()
    if pending:
        raise HTTPException(
            status_code=400,
            detail=f"{len(pending)} recommendations still pending review"
        )

    before = {"status": plan.status}
    plan.status = "final"

    audit = AuditLog(
        actor=reviewer,
        action="finalize",
        entity="plan_run",
        entity_id=plan_id,
        before_state=before,
        after_state={"status": "final"},
    )
    session.add(audit)
    await session.commit()
    return {"status": "ok", "plan_id": plan_id, "new_status": "final"}


@router.get("/audit")
async def get_audit(session: AsyncSession = Depends(get_session)):
    """Return the append-only audit timeline."""
    result = await session.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(100)
    )
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "actor": log.actor,
            "action": log.action,
            "entity": log.entity,
            "entity_id": log.entity_id,
            "before_state": log.before_state,
            "after_state": log.after_state,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
