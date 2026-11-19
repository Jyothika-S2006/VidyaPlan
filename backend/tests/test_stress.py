"""Tests for the Monte Carlo stress-test and VOI modules."""
import pytest
from app.solver.stress import estimate_p_gap, run_stress_test
from app.solver.voi import compute_voi
from app.solver.scenarios import compare_scenarios, marginal_view
from app.solver.baselines import run_baselines
from app.solver.model import solve


def _items(n=5, cost=100000, priority=0.9, facility="computers", elec="CONFIRMED_OK"):
    return [
        {
            "id": f"{i}_{facility}",
            "school_id": i,
            "school_name": f"School {i}",
            "facility": facility,
            "cost": cost,
            "priority": priority,
            "electricity_state": elec,
            "district": "04",
        }
        for i in range(n)
    ]


def test_p_gap_fallback_to_state():
    missing = [{"school_id": 99, "district": "ZZ", "facility": "electricity"}]
    all_ev = [
        {"school_id": 1, "district": "01", "facility": "electricity", "state": "CONFIRMED_GAP"},
        {"school_id": 2, "district": "01", "facility": "electricity", "state": "CONFIRMED_OK"},
        {"school_id": 3, "district": "01", "facility": "electricity", "state": "CONFIRMED_OK"},
        {"school_id": 4, "district": "01", "facility": "electricity", "state": "CONFIRMED_OK"},
    ]
    p = estimate_p_gap(missing, all_ev, "electricity")
    assert 0 < p["99"] < 1


def test_p_gap_in_range():
    missing = [{"school_id": 1, "district": "04", "facility": "library"}]
    all_ev = [
        {"school_id": 10, "district": "04", "facility": "library", "state": "CONFIRMED_GAP"},
        {"school_id": 11, "district": "04", "facility": "library", "state": "CONFIRMED_OK"},
        {"school_id": 12, "district": "04", "facility": "library", "state": "CONFIRMED_GAP"},
        {"school_id": 13, "district": "04", "facility": "library", "state": "CONFIRMED_OK"},
    ]
    p = estimate_p_gap(missing, all_ev, "library")
    assert 0.0 <= p["1"] <= 1.0


def test_stress_robustness_in_range():
    items = _items(5, cost=100000, priority=0.9)
    budget = 300000
    base = solve(items, budget)
    base_ids = {i["id"] for i in base["selected"]}

    result = run_stress_test(
        base_selected_ids=base_ids,
        base_objective=base["objective"],
        eligible_items=items,
        missing_items=[],
        p_gap={},
        budget=budget,
        n_scenarios=20,
        seed=42,
    )
    for rob in result.robustness.values():
        assert 0.0 <= rob <= 1.0


def test_stress_regret_non_negative():
    items = _items(5, cost=100000, priority=0.9)
    budget = 300000
    base = solve(items, budget)
    base_ids = {i["id"] for i in base["selected"]}

    result = run_stress_test(
        base_selected_ids=base_ids,
        base_objective=base["objective"],
        eligible_items=items,
        missing_items=[],
        p_gap={},
        budget=budget,
        n_scenarios=20,
        seed=42,
    )
    assert result.expected_regret_rs >= 0.0
    assert result.expected_regret_pct >= 0.0


def test_stress_deterministic():
    items = _items(6, cost=100000, priority=0.9)
    budget = 400000
    base = solve(items, budget)
    base_ids = {i["id"] for i in base["selected"]}

    r1 = run_stress_test(base_ids, base["objective"], items, [], {}, budget, 50, 42)
    r2 = run_stress_test(base_ids, base["objective"], items, [], {}, budget, 50, 42)
    assert r1.robustness == r2.robustness
    assert r1.expected_regret_rs == r2.expected_regret_rs


def test_voi_zero_when_no_missing():
    items = _items(5, cost=100000, priority=0.9)
    budget = 300000
    base = solve(items, budget)
    entries = compute_voi(items, [], [], {}, budget, base["objective"])
    assert entries == []


def test_scenarios_compare_has_three():
    items = _items(10, cost=100000, priority=0.9)
    r = compare_scenarios(items, 500000)
    assert r.base.budget == 500000
    assert abs(r.low.budget - 350000) < 1
    assert abs(r.high.budget - 650000) < 1


def test_marginal_view():
    items = _items(10, cost=100000, priority=0.9)
    r = marginal_view(items, 300000, extra=100000)
    assert r.base_budget == 300000
    assert r.extra_budget == 100000
    assert r.delta_interventions >= 0


def test_baselines_all_methods():
    items = _items(8, cost=100000, priority=0.9)
    budget = 400000
    opt = solve(items, budget)
    results = run_baselines(items, budget, opt, n_random=20, seed=42)
    methods = {r.method for r in results}
    assert methods == {"optimiser", "greedy", "random_avg"}
    for r in results:
        assert r.budget_used <= budget + 1


def test_greedy_pct_bounded():
    items = _items(8, cost=100000, priority=0.9)
    budget = 400000
    opt = solve(items, budget)
    results = run_baselines(items, budget, opt, n_random=20, seed=42)
    greedy = next(r for r in results if r.method == "greedy")
    assert 0.0 <= greedy.pct_vs_optimiser <= 100.0 + 0.1  # small float tolerance
