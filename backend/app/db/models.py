"""SQLAlchemy ORM models for VidyaPlan."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String, Text, JSON, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class School(Base):
    """A school in the dataset."""
    __tablename__ = "schools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(256))
    district: Mapped[Optional[str]] = mapped_column(String(128))
    block: Mapped[Optional[str]] = mapped_column(String(128))
    enrollment: Mapped[Optional[int]] = mapped_column(Integer)
    in_cohort: Mapped[bool] = mapped_column(Boolean, default=False)
    observation_year: Mapped[str] = mapped_column(String(16), default="2017-18")

    evidence: Mapped[list["FacilityEvidence"]] = relationship(back_populates="school")


class FacilityEvidence(Base):
    """Evidence state for a (school, facility) pair."""
    __tablename__ = "facility_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), index=True)
    facility: Mapped[str] = mapped_column(String(32))  # electricity, library, computers
    state: Mapped[str] = mapped_column(String(32))     # CONFIRMED_GAP, CONFIRMED_OK, MISSING, UNRELIABLE
    raw_value: Mapped[Optional[str]] = mapped_column(String(64))
    reason_code: Mapped[Optional[str]] = mapped_column(String(64))
    observation_year: Mapped[str] = mapped_column(String(16), default="2017-18")

    school: Mapped["School"] = relationship(back_populates="evidence")


class DataQualityLog(Base):
    """Log of fields dropped during cleaning."""
    __tablename__ = "data_quality_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    field: Mapped[str] = mapped_column(String(128))
    reason: Mapped[str] = mapped_column(Text)
    rows_affected: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class PlanRun(Base):
    """A single solver run."""
    __tablename__ = "plan_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    budget: Mapped[float] = mapped_column(Float)
    objective: Mapped[float] = mapped_column(Float, default=0.0)
    budget_used: Mapped[float] = mapped_column(Float, default=0.0)
    seed: Mapped[int] = mapped_column(Integer, default=42)
    status: Mapped[str] = mapped_column(String(32), default="draft")  # draft, in_review, final
    params: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="plan_run")


class Recommendation(Base):
    """A single funded or deferred item in a plan."""
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_run_id: Mapped[int] = mapped_column(ForeignKey("plan_runs.id"), index=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"))
    facility_type: Mapped[str] = mapped_column(String(32))  # library, electricity, computers
    cost: Mapped[float] = mapped_column(Float)
    priority: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32))  # selected, deferred
    reason_code: Mapped[Optional[str]] = mapped_column(String(64))
    robustness: Mapped[Optional[float]] = mapped_column(Float)
    review_status: Mapped[str] = mapped_column(String(32), default="pending")  # pending, approved, rejected
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    explanation_source: Mapped[str] = mapped_column(String(16), default="template")

    plan_run: Mapped["PlanRun"] = relationship(back_populates="recommendations")
    school: Mapped["School"] = relationship()
    reviews: Mapped[list["Review"]] = relationship(back_populates="recommendation")


class Review(Base):
    """Human review decision for a recommendation."""
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recommendation_id: Mapped[int] = mapped_column(ForeignKey("recommendations.id"), index=True)
    decision: Mapped[str] = mapped_column(String(16))  # approved, rejected
    note: Mapped[Optional[str]] = mapped_column(Text)
    reviewer: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    recommendation: Mapped["Recommendation"] = relationship(back_populates="reviews")


class AuditLog(Base):
    """Append-only audit trail."""
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor: Mapped[str] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(64))
    entity: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[Optional[int]] = mapped_column(Integer)
    before_state: Mapped[Optional[dict]] = mapped_column(JSON)
    after_state: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class AgentTrace(Base):
    """Trace of agent pipeline steps."""
    __tablename__ = "agent_trace"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("plan_runs.id"))
    agent: Mapped[str] = mapped_column(String(64))
    input_hash: Mapped[Optional[str]] = mapped_column(String(64))
    tool_called: Mapped[Optional[str]] = mapped_column(String(64))
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(16), default="template")  # granite, template
    output_summary: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
