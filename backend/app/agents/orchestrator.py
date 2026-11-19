"""Agent pipeline orchestrator.

Pipeline: Evidence Agent -> Portfolio Agent -> Stress (optional) -> Trade-off Agent
Every step is recorded to agent_trace with agent name, input hash,
tool called, latency, and source (granite/template).
"""
import hashlib
import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TraceStep:
    """One step in the agent pipeline trace."""
    agent: str
    input_hash: str
    tool_called: str | None
    latency_ms: int
    source: str   # "granite" | "template" | "solver"
    output_summary: str
    plan_run_id: int | None = None


@dataclass
class OrchestratorResult:
    """Full result of one orchestrator run."""
    plan_id: int | None
    trace: list[TraceStep] = field(default_factory=list)
    school_notes: dict[int, dict] = field(default_factory=dict)  # school_id -> {note, source}
    item_rationales: list[dict] = field(default_factory=list)
    stress_result: dict | None = None
    voi_entries: list | None = None


def _hash(obj) -> str:
    return hashlib.md5(str(obj).encode()).hexdigest()[:12]


def _persist_step(step: "TraceStep") -> None:
    """Persist a single trace step to DB immediately (best-effort)."""
    if step.plan_run_id is None:
        return
    try:
        import asyncio
        from app.db.models import AgentTrace as AgentTraceModel
        from app.db.session import AsyncSessionLocal

        async def _save():
            async with AsyncSessionLocal() as s:
                s.add(AgentTraceModel(
                    plan_run_id=step.plan_run_id,
                    agent=step.agent,
                    input_hash=step.input_hash,
                    tool_called=step.tool_called,
                    latency_ms=step.latency_ms,
                    source=step.source,
                    output_summary=step.output_summary,
                ))
                await s.commit()

        loop = asyncio.new_event_loop()
        loop.run_until_complete(_save())
        loop.close()
    except Exception as exc:
        logger.warning("Failed to persist trace step %s: %s", step.agent, exc)


def run_pipeline(
    plan_id: int | None,
    schools: list[dict],
    selected: list[dict],
    deferred: list[dict],
    budget: float,
    budget_used: float,
    run_stress: bool = False,
    n_scenarios: int = 50,
) -> OrchestratorResult:
    """
    Run the full Evidence -> Trade-off agent pipeline.

    Each trace step is persisted to DB immediately after it completes so the
    frontend can poll and see partial progress.
    """
    from app.agents.evidence_agent import generate_school_note, reset_granite_counter
    from app.agents.tradeoff_agent import generate_batch_rationales
    from app.agents.granite_client import reset_circuit_breaker

    # Reset per-run counters so each fresh plan run can try Granite
    reset_circuit_breaker()
    reset_granite_counter()
    result = OrchestratorResult(plan_id=plan_id)

    # ── Step 1: Evidence Agent ────────────────────────────────────────────
    t0 = time.time()
    school_notes: dict[int, dict] = {}
    for school in schools[:40]:  # cap to cohort size
        note, source = generate_school_note(
            school_name=school.get("name", f"School {school['id']}"),
            district=school.get("district"),
            evidence=school.get("evidence", {}),
            eligibility=school.get("eligibility", {}),
        )
        school_notes[school["id"]] = {"note": note, "source": source}

    step1 = TraceStep(
        agent="evidence_agent",
        input_hash=_hash(schools),
        tool_called=None,
        latency_ms=int((time.time() - t0) * 1000),
        source="template",
        output_summary=f"Generated notes for {len(school_notes)} schools",
        plan_run_id=plan_id,
    )
    result.trace.append(step1)
    result.school_notes = school_notes
    _persist_step(step1)  # save immediately so frontend can see it

    # ── Step 2: Trade-off Agent ───────────────────────────────────────────
    t0 = time.time()
    rationales = generate_batch_rationales(selected, deferred, budget_used, budget)
    granite_count = sum(1 for r in rationales if r.get("explanation_source") == "granite")
    step2 = TraceStep(
        agent="tradeoff_agent",
        input_hash=_hash(selected + deferred),
        tool_called=None,
        latency_ms=int((time.time() - t0) * 1000),
        source="granite" if granite_count > 0 else "template",
        output_summary=f"Rationales for {len(rationales)} items ({granite_count} via Granite)",
        plan_run_id=plan_id,
    )
    result.trace.append(step2)
    result.item_rationales = rationales
    _persist_step(step2)  # save immediately

    return result
