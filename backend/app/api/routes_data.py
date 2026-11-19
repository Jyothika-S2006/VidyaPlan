"""API routes for data summary, quality and school listing."""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.db.models import School, FacilityEvidence, DataQualityLog

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/data/summary")
async def data_summary(session: AsyncSession = Depends(get_session)):
    """Return counts by evidence state, observation year, and cohort info."""
    total_schools = await session.scalar(select(func.count(School.id)))
    cohort_schools = await session.scalar(
        select(func.count(School.id)).where(School.in_cohort == True)
    )
    # Evidence state counts per facility
    result = await session.execute(
        select(
            FacilityEvidence.facility,
            FacilityEvidence.state,
            func.count().label("count")
        )
        .join(School, School.id == FacilityEvidence.school_id)
        .where(School.in_cohort == True)
        .group_by(FacilityEvidence.facility, FacilityEvidence.state)
    )
    evidence_counts = {}
    for row in result:
        if row.facility not in evidence_counts:
            evidence_counts[row.facility] = {}
        evidence_counts[row.facility][row.state] = row.count

    return {
        "total_schools": total_schools or 0,
        "cohort_schools": cohort_schools or 0,
        "observation_year": "2017-18",
        "evidence_counts": evidence_counts,
    }


@router.get("/data/quality")
async def data_quality(session: AsyncSession = Depends(get_session)):
    """Return dropped fields and reasons from data_quality_log."""
    result = await session.execute(select(DataQualityLog).order_by(DataQualityLog.created_at.desc()))
    logs = result.scalars().all()
    return [
        {"field": log.field, "reason": log.reason, "rows_affected": log.rows_affected}
        for log in logs
    ]


@router.get("/schools")
async def list_schools(
    district: Optional[str] = Query(None),
    in_cohort: Optional[bool] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """Return schools with evidence chips, filterable by district and cohort membership."""
    q = select(School)
    if district:
        q = q.where(School.district == district)
    if in_cohort is not None:
        q = q.where(School.in_cohort == in_cohort)
    result = await session.execute(q.limit(500))
    schools = result.scalars().all()

    output = []
    for school in schools:
        ev_result = await session.execute(
            select(FacilityEvidence).where(FacilityEvidence.school_id == school.id)
        )
        evidence = {e.facility: e.state for e in ev_result.scalars().all()}
        output.append({
            "id": school.id,
            "external_id": school.external_id,
            "name": school.name,
            "district": school.district,
            "block": school.block,
            "enrollment": school.enrollment,
            "in_cohort": school.in_cohort,
            "observation_year": school.observation_year,
            "evidence": evidence,
        })
    return output
