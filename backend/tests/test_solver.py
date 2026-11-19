"""Tests for the OR-Tools CP-SAT solver."""
import pytest
from app.solver.model import solve


def _make_items(n: int, cost: float = 100000, priority: float = 1.0) -> list:
    return [
        {
            "id": f"{i}_electricity",
            "school_id": i,
            "school_name": f"School {i}",
            "facility": "electricity",
            "cost": cost,
            "priority": priority,
            "electricity_state": "CONFIRMED_GAP",
        }
        for i in range(n)
    ]


def test_budget_never_exceeded():
    items = _make_items(10, cost=100000)
    result = solve(items, budget=350000)
    assert result["budget_used"] <= 350000


def test_deterministic():
    items = _make_items(5, cost=100000)
    r1 = solve(items, budget=250000, seed=42)
    r2 = solve(items, budget=250000, seed=42)
    assert [i["id"] for i in r1["selected"]] == [i["id"] for i in r2["selected"]]


def test_empty_items():
    result = solve([], budget=1000000)
    assert result["selected"] == []
    assert result["deferred"] == []
    assert result["budget_used"] == 0


def test_all_deferred_when_budget_zero():
    items = _make_items(3, cost=100000)
    result = solve(items, budget=1)
    assert len(result["selected"]) == 0
    assert len(result["deferred"]) == 3


def test_computers_dependency():
    """Computers should not be selected without electricity when electricity is a gap."""
    items = [
        {
            "id": "1_electricity",
            "school_id": 1,
            "school_name": "School 1",
            "facility": "electricity",
            "cost": 250000,
            "priority": 1.0,
            "electricity_state": "CONFIRMED_GAP",
        },
        {
            "id": "1_computers",
            "school_id": 1,
            "school_name": "School 1",
            "facility": "computers",
            "cost": 400000,
            "priority": 0.9,
            "electricity_state": "CONFIRMED_GAP",
        },
    ]
    result = solve(items, budget=400000)
    selected_facilities = [i["facility"] for i in result["selected"]]
    if "computers" in selected_facilities:
        assert "electricity" in selected_facilities
