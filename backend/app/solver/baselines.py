"""Baseline comparison: optimiser vs greedy vs random.

Implements:
(a) Greedy: sort by priority/cost ratio, pick greedily respecting the
    electricity->computers dependency. This is what most naive tools do.
(b) Random: average of 200 random feasible plans (seeded). A feasible
    plan never exceeds budget and respects the dependency.

Both are compared to the CP-SAT optimiser result.
Report objective, interventions funded, schools improved, budget used,
and % difference vs optimiser. Report real numbers only — do not fabricate.
"""
import logging
import random
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BaselineResult:
    """Result for one baseline method."""
    method: str                   # "optimiser", "greedy", "random_avg"
    objective: float
    interventions_funded: int
    schools_improved: int
    budget_used: float
    pct_vs_optimiser: float | None  # None for optimiser itself
    provenance: str = "SIMULATED"


def run_baselines(
    items: list[dict],
    budget: float,
    optimiser_result: dict,
    n_random: int = 200,
    seed: int = 42,
) -> list[BaselineResult]:
    """
    Compute baseline comparisons for a given set of eligible items.

    Args:
        items: eligible items (same format as solve()).
        budget: total budget in Rs.
        optimiser_result: result dict from solve() — the CP-SAT optimal plan.
        n_random: number of random plans to average.
        seed: random seed for reproducibility.

    Returns:
        List of BaselineResult for optimiser, greedy and random_avg.
    """
    opt_obj = optimiser_result["objective"]
    opt_funded = len(optimiser_result["selected"])
    opt_schools = len({i["school_id"] for i in optimiser_result["selected"]})
    opt_used = optimiser_result["budget_used"]

    optimiser = BaselineResult(
        method="optimiser",
        objective=round(opt_obj, 4),
        interventions_funded=opt_funded,
        schools_improved=opt_schools,
        budget_used=round(opt_used, 0),
        pct_vs_optimiser=100.0,
    )

    greedy = _greedy_baseline(items, budget, opt_obj)
    rnd = _random_baseline(items, budget, opt_obj, n_random, seed)

    return [optimiser, greedy, rnd]


def _greedy_baseline(items: list[dict], budget: float, opt_obj: float) -> BaselineResult:
    """Greedy: pick by priority/cost ratio, respect dependency."""
    sorted_items = sorted(
        items,
        key=lambda x: x["priority"] / max(x["cost"], 1),
        reverse=True,
    )
    selected: list[dict] = []
    budget_used = 0.0
    objective = 0.0
    funded_by_school: dict[int, set] = {}

    for item in sorted_items:
        sid = item["school_id"]
        facility = item["facility"]

        # Electricity-computers dependency
        if facility == "computers":
            elec_state = item.get("electricity_state", "MISSING")
            if elec_state == "CONFIRMED_GAP":
                already_funded_elec = "electricity" in funded_by_school.get(sid, set())
                if not already_funded_elec:
                    continue  # skip — electricity not funded yet

        if budget_used + item["cost"] <= budget:
            selected.append(item)
            budget_used += item["cost"]
            objective += item["priority"]
            if sid not in funded_by_school:
                funded_by_school[sid] = set()
            funded_by_school[sid].add(facility)

    schools_improved = len({i["school_id"] for i in selected})
    pct = round(objective / opt_obj * 100, 1) if opt_obj > 0 else 0.0

    return BaselineResult(
        method="greedy",
        objective=round(objective, 4),
        interventions_funded=len(selected),
        schools_improved=schools_improved,
        budget_used=round(budget_used, 0),
        pct_vs_optimiser=pct,
    )


def _random_baseline(
    items: list[dict],
    budget: float,
    opt_obj: float,
    n_random: int,
    seed: int,
) -> BaselineResult:
    """Average of n_random random feasible plans."""
    rng = random.Random(seed)
    obj_sum = 0.0
    funded_sum = 0
    schools_sum = 0
    used_sum = 0.0

    for _ in range(n_random):
        shuffled = items[:]
        rng.shuffle(shuffled)
        selected: list[dict] = []
        budget_used = 0.0
        objective = 0.0
        funded_by_school: dict[int, set] = {}

        for item in shuffled:
            sid = item["school_id"]
            facility = item["facility"]
            if facility == "computers":
                elec_state = item.get("electricity_state", "MISSING")
                if elec_state == "CONFIRMED_GAP":
                    if "electricity" not in funded_by_school.get(sid, set()):
                        continue
            if budget_used + item["cost"] <= budget:
                selected.append(item)
                budget_used += item["cost"]
                objective += item["priority"]
                if sid not in funded_by_school:
                    funded_by_school[sid] = set()
                funded_by_school[sid].add(facility)

        obj_sum += objective
        funded_sum += len(selected)
        schools_sum += len({i["school_id"] for i in selected})
        used_sum += budget_used

    n = max(n_random, 1)
    avg_obj = obj_sum / n
    pct = round(avg_obj / opt_obj * 100, 1) if opt_obj > 0 else 0.0

    return BaselineResult(
        method="random_avg",
        objective=round(avg_obj, 4),
        interventions_funded=round(funded_sum / n, 1),
        schools_improved=round(schools_sum / n, 1),
        budget_used=round(used_sum / n, 0),
        pct_vs_optimiser=pct,
    )
