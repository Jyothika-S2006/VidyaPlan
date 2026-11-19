"""Monte Carlo stress-test for plan robustness.

Algorithm:
1. For each MISSING facility field, estimate P(gap) from known schools
   in the same district (fallback: state-wide rate). Smooth with a
   Laplace prior (add-1 smoothing).
2. Run N scenarios (default 300). In each:
   - Sample every MISSING field as gap / not-gap using P(gap).
   - Build the augmented eligible-items list.
   - Solve the augmented problem at the same budget.
3. Robustness of a base-plan pick = fraction of scenarios where that
   item appears in the optimal solution.
4. Expected regret = mean(scenario_optimal_value - base_plan_value).
   Reported as absolute Rs. and as % of base plan value.

All outputs are labelled SIMULATED. Seed and N are recorded.
"""
import logging
import random
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class StressResult:
    """Result of the Monte Carlo stress-test."""
    plan_id: int
    n_scenarios: int
    seed: int
    robustness: dict[str, float]          # item_id -> robustness in [0, 1]
    robustness_band: dict[str, str]       # item_id -> "green"|"amber"|"red"
    expected_regret_rs: float             # mean(scenario_opt - base) in Rs equivalent
    expected_regret_pct: float            # as % of base plan objective
    base_objective: float
    provenance: str = "SIMULATED"
    details: list[dict] = field(default_factory=list)  # per-pick detail rows


def estimate_p_gap(
    missing_schools: list[dict],
    all_evidence: list[dict],
    facility: str,
) -> dict[str, float]:
    """
    Estimate P(gap) for each MISSING school-facility pair.

    Uses district-level gap rate among known schools (CONFIRMED_GAP or
    CONFIRMED_OK). Falls back to state-wide rate if district has fewer
    than 3 known records. Laplace (add-1) smoothing applied.

    Args:
        missing_schools: list of dicts with keys school_id, district, facility.
        all_evidence: list of dicts with keys school_id, district, facility,
                      state.
        facility: the facility type being estimated.

    Returns:
        Dict mapping school_id -> P(gap) float in [0, 1].
    """
    # Count known gaps per district for this facility
    district_counts: dict[str, dict] = {}  # district -> {gap: int, total: int}
    state_gap = 0
    state_total = 0

    for ev in all_evidence:
        if ev.get("facility") != facility:
            continue
        state = ev.get("state", "")
        if state not in ("CONFIRMED_GAP", "CONFIRMED_OK"):
            continue
        district = ev.get("district") or "unknown"
        if district not in district_counts:
            district_counts[district] = {"gap": 0, "total": 0}
        district_counts[district]["total"] += 1
        state_total += 1
        if state == "CONFIRMED_GAP":
            district_counts[district]["gap"] += 1
            state_gap += 1

    # State-wide rate with Laplace smoothing
    state_p = (state_gap + 1) / (state_total + 2)

    result: dict[str, float] = {}
    for school in missing_schools:
        district = school.get("district") or "unknown"
        counts = district_counts.get(district, {})
        d_total = counts.get("total", 0)
        d_gap = counts.get("gap", 0)
        if d_total >= 3:
            # District rate with Laplace smoothing
            p = (d_gap + 1) / (d_total + 2)
        else:
            p = state_p
        result[str(school["school_id"])] = round(p, 4)

    return result


def run_stress_test(
    base_selected_ids: set[str],
    base_objective: float,
    eligible_items: list[dict],
    missing_items: list[dict],
    p_gap: dict[str, float],
    budget: float,
    n_scenarios: int = 300,
    seed: int = 42,
) -> StressResult:
    """
    Run Monte Carlo stress-test.

    Args:
        base_selected_ids: set of item ids selected in the base plan.
        base_objective: objective value of the base plan.
        eligible_items: items already eligible (CONFIRMED_GAP).
        missing_items: items from MISSING fields (each has school_id, facility,
                       cost, priority, electricity_state).
        p_gap: dict mapping str(school_id) -> P(gap) for MISSING fields.
        budget: total budget in Rs.
        n_scenarios: number of Monte Carlo scenarios.
        seed: random seed for reproducibility.

    Returns:
        StressResult with per-pick robustness and expected regret.
    """
    from app.solver.model import solve

    rng = random.Random(seed)
    # Count how many times each base pick appears in scenario optima
    pick_counts: dict[str, int] = {item_id: 0 for item_id in base_selected_ids}
    regrets: list[float] = []

    for _ in range(n_scenarios):
        # Sample MISSING fields: each becomes gap or not-gap
        scenario_extra: list[dict] = []
        for item in missing_items:
            sid = str(item["school_id"])
            p = p_gap.get(sid, 0.3)
            if rng.random() < p:
                # This missing field is a gap in this scenario — add to eligible
                scenario_extra.append(item)

        scenario_items = eligible_items + scenario_extra
        if not scenario_items:
            regrets.append(0.0)
            continue

        result = solve(scenario_items, budget, seed=rng.randint(0, 999999))
        scenario_opt = result["objective"]

        # Track which base picks are in this scenario's optimum
        scenario_selected_ids = {i["id"] for i in result["selected"]}
        for item_id in base_selected_ids:
            if item_id in scenario_selected_ids:
                pick_counts[item_id] += 1

        regrets.append(max(0.0, scenario_opt - base_objective))

    # Compute robustness
    robustness: dict[str, float] = {}
    robustness_band: dict[str, str] = {}
    details: list[dict] = []

    for item_id in base_selected_ids:
        rob = pick_counts[item_id] / n_scenarios if n_scenarios > 0 else 0.0
        robustness[item_id] = round(rob, 4)
        band = "green" if rob >= 0.85 else ("amber" if rob >= 0.60 else "red")
        robustness_band[item_id] = band
        details.append({
            "item_id": item_id,
            "robustness": round(rob, 4),
            "band": band,
            "fragile": band == "red",
        })

    expected_regret = sum(regrets) / len(regrets) if regrets else 0.0
    regret_pct = (expected_regret / base_objective * 100) if base_objective > 0 else 0.0

    return StressResult(
        plan_id=0,
        n_scenarios=n_scenarios,
        seed=seed,
        robustness=robustness,
        robustness_band=robustness_band,
        expected_regret_rs=round(expected_regret, 2),
        expected_regret_pct=round(regret_pct, 2),
        base_objective=base_objective,
        details=details,
    )
