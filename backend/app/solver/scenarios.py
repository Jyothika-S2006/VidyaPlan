"""Budget scenario comparison and marginal view.

Implements:
1. compare(budget): solve at B, 0.7*B, 1.3*B and return side-by-side diff
   with items gained/lost between scenarios.
2. marginal(budget, extra): solve at B and B+extra, return the diff — what
   the next chunk of budget funds.

All outputs labelled SIMULATED.
"""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ScenarioResult:
    """Result for one budget scenario."""
    label: str
    budget: float
    budget_used: float
    objective: float
    interventions_funded: int
    schools_improved: int
    selected_ids: set
    selected: list[dict]
    deferred: list[dict]
    provenance: str = "SIMULATED"


@dataclass
class ScenarioCompare:
    """Side-by-side comparison of three budget scenarios."""
    base: ScenarioResult
    low: ScenarioResult    # 0.7 * base budget
    high: ScenarioResult   # 1.3 * base budget
    gained_in_high: list[dict]   # items in high but not in base
    lost_in_low: list[dict]      # items in base but not in low
    provenance: str = "SIMULATED"


@dataclass
class MarginalResult:
    """What the next Rs. X funds."""
    base_budget: float
    extra_budget: float
    new_items: list[dict]   # items funded at B+extra but not at B
    delta_objective: float
    delta_interventions: int
    delta_schools: int
    provenance: str = "SIMULATED"


def _run_scenario(items: list[dict], budget: float, label: str) -> ScenarioResult:
    """Run solver for one budget and wrap the result."""
    from app.solver.model import solve
    result = solve(items, budget)
    selected_ids = {i["id"] for i in result["selected"]}
    schools_improved = len({i["school_id"] for i in result["selected"]})
    return ScenarioResult(
        label=label,
        budget=budget,
        budget_used=result["budget_used"],
        objective=result["objective"],
        interventions_funded=len(result["selected"]),
        schools_improved=schools_improved,
        selected_ids=selected_ids,
        selected=result["selected"],
        deferred=result["deferred"],
    )


def compare_scenarios(items: list[dict], budget: float) -> ScenarioCompare:
    """
    Solve at B, 0.7*B, 1.3*B and return a side-by-side comparison.

    Args:
        items: eligible items list (same format as solve()).
        budget: base budget in Rs.

    Returns:
        ScenarioCompare with base/low/high results and gained/lost item lists.
    """
    base = _run_scenario(items, budget, "Base (B)")
    low = _run_scenario(items, budget * 0.7, "Low (-30%)")
    high = _run_scenario(items, budget * 1.3, "High (+30%)")

    item_map = {i["id"]: i for i in items}
    gained_in_high = [item_map[iid] for iid in high.selected_ids - base.selected_ids if iid in item_map]
    lost_in_low = [item_map[iid] for iid in base.selected_ids - low.selected_ids if iid in item_map]

    return ScenarioCompare(
        base=base,
        low=low,
        high=high,
        gained_in_high=gained_in_high,
        lost_in_low=lost_in_low,
    )


def marginal_view(items: list[dict], budget: float, extra: float = 1_000_000) -> MarginalResult:
    """
    Show what the next `extra` Rs. would fund.

    Args:
        items: eligible items list.
        budget: current budget.
        extra: additional budget increment (default Rs. 10 lakh).

    Returns:
        MarginalResult listing new items funded and the improvement.
    """
    from app.solver.model import solve

    base_result = solve(items, budget)
    high_result = solve(items, budget + extra)

    base_ids = {i["id"] for i in base_result["selected"]}
    high_ids = {i["id"] for i in high_result["selected"]}
    new_ids = high_ids - base_ids

    item_map = {i["id"]: i for i in items}
    new_items = [item_map[iid] for iid in new_ids if iid in item_map]
    delta_schools = len({i["school_id"] for i in new_items})

    return MarginalResult(
        base_budget=budget,
        extra_budget=extra,
        new_items=new_items,
        delta_objective=round(high_result["objective"] - base_result["objective"], 4),
        delta_interventions=len(new_items),
        delta_schools=delta_schools,
    )
