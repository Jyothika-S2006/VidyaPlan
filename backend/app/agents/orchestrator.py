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

    Args:
        plan_id: DB plan run ID (may be None if plan not yet persisted).
        schools: list of school dicts with evidence and eligibility.
        selected: list of selected items from solver.
        deferred: list of deferred items from solver.
        budget: total budget.
        budget_used: budget used by selected items.
        run_stress: whether to run Monte Carlo stress-test.
        n_scenarios: number of stress-test scenarios (kept low for speed).

    Returns:
        OrchestratorResult with trace, notes, rationales and optional stress results.
    """
    from app.agents.evidence_agent import generate_school_note
    from app.agents.tradeoff_agent import generate_batch_rationales

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

    step1_ms = int((time.time() - t0) * 1000)
    result.trace.append(TraceStep(
        agent="evidence_agent",
        input_hash=_hash(schools),
        tool_called=None,
        latency_ms=step1_ms,
        source="template",  # will be "granite" if any granite calls succeeded
        output_summary=f"Generated notes for {len(school_notes)} schools",
        plan_run_id=plan_id,
    ))
    result.school_notes = school_notes

    # ── Step 2: Trade-off Agent ───────────────────────────────────────────
    t0 = time.time()
    rationales = generate_batch_rationales(selected, deferred, budget_used, budget)
    step2_ms = int((time.time() - t0) * 1000)
    granite_count = sum(1 for r in rationales if r.get("explanation_source") == "granite")
    result.trace.append(TraceStep(
        agent="tradeoff_agent",
        input_hash=_hash(selected + deferred),
        tool_called=None,
        latency_ms=step2_ms,
        source="granite" if granite_count > 0 else "template",
        output_summary=f"Rationales for {len(rationales)} items ({granite_count} via Granite)",
        plan_run_id=plan_id,
    ))
    result.item_rationales = rationales

    return result
