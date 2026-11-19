"""OR-Tools CP-SAT solver for budget-constrained infrastructure planning."""
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    logger.warning("OR-Tools not available, using greedy fallback solver.")


def solve(items: list[dict[str, Any]], budget: float, seed: int = 42) -> dict:
    """
    Solve the budget-constrained infrastructure planning problem.

    Args:
        items: List of eligible items with keys: id, school_id, school_name,
               facility, cost, priority, electricity_state.
        budget: Total budget in INR.
        seed: Random seed for deterministic tie-breaking.

    Returns:
        dict with keys: selected, deferred, budget_used, objective.
    """
    if not items:
        return {"selected": [], "deferred": [], "budget_used": 0.0, "objective": 0.0}

    if ORTOOLS_AVAILABLE:
        return _solve_cpsat(items, budget, seed)
    else:
        return _solve_greedy(items, budget)


def _solve_cpsat(items: list[dict], budget: float, seed: int) -> dict:
    """Solve using OR-Tools CP-SAT integer programming."""
    SCALE = 1000  # Scale to integers

    model = cp_model.CpModel()
    x = [model.new_bool_var(f"x_{i}") for i in range(len(items))]

    # Budget constraint
    scaled_budget = int(budget * SCALE)
    scaled_costs = [int(item["cost"] * SCALE) for item in items]
    model.add(sum(scaled_costs[i] * x[i] for i in range(len(items))) <= scaled_budget)

    # Electricity-computers dependency constraint
    school_indices: dict = {}
    for i, item in enumerate(items):
        sid = item["school_id"]
        if sid not in school_indices:
            school_indices[sid] = {}
        school_indices[sid][item["facility"]] = i

    for sid, fac_map in school_indices.items():
        if "computers" in fac_map and "electricity" in fac_map:
            # computers can only be selected if electricity is also selected
            if items[fac_map["electricity"]]["electricity_state"] == "CONFIRMED_GAP":
                model.add(x[fac_map["computers"]] <= x[fac_map["electricity"]])

    # Objective: maximise sum of priorities
    scaled_priorities = [int(item["priority"] * SCALE) for item in items]
    model.maximize(sum(scaled_priorities[i] * x[i] for i in range(len(items))))

    solver = cp_model.CpSolver()
    solver.parameters.random_seed = seed
    solver.parameters.num_workers = 1
    status = solver.solve(model)

    selected = []
    deferred = []
    budget_used = 0.0
    objective = 0.0

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for i, item in enumerate(items):
            if solver.value(x[i]):
                selected.append(item)
                budget_used += item["cost"]
                objective += item["priority"]
            else:
                deferred.append({**item, "reason_code": _reason_code(item, selected, budget, budget_used)})
    else:
        deferred = [{**item, "reason_code": "OUT_OF_BUDGET"} for item in items]

    return {
        "selected": selected,
        "deferred": deferred,
        "budget_used": budget_used,
        "objective": objective,
    }


def _solve_greedy(items: list[dict], budget: float) -> dict:
    """Greedy fallback: sort by priority/cost ratio, select greedily."""
    sorted_items = sorted(items, key=lambda x: x["priority"] / x["cost"], reverse=True)
    selected = []
    deferred = []
    budget_used = 0.0
    objective = 0.0
    selected_schools_facilities: dict = {}

    for item in sorted_items:
        sid = item["school_id"]
        # Check electricity dependency
        if item["facility"] == "computers":
            elec_funded = selected_schools_facilities.get(sid, {}).get("electricity", False)
            elec_state = item.get("electricity_state", "MISSING")
            if elec_state == "CONFIRMED_GAP" and not elec_funded:
                deferred.append({**item, "reason_code": "BLOCKED_PREREQ_UNVERIFIED"})
                continue

        if budget_used + item["cost"] <= budget:
            selected.append(item)
            budget_used += item["cost"]
            objective += item["priority"]
            if sid not in selected_schools_facilities:
                selected_schools_facilities[sid] = {}
            selected_schools_facilities[sid][item["facility"]] = True
        else:
            deferred.append({**item, "reason_code": "OUT_OF_BUDGET"})

    return {"selected": selected, "deferred": deferred, "budget_used": budget_used, "objective": objective}


def _reason_code(item: dict, selected: list[dict], budget: float, budget_used: float) -> str:
    """Determine reason code for a deferred item."""
    if budget_used + item["cost"] > budget:
        return "OUT_OF_BUDGET"
    return "LOWER_PRIORITY_PER_RUPEE"
