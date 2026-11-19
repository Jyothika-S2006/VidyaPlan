"""Tests for the agent modules — with mocked Granite client."""
import pytest
from unittest.mock import patch

from app.agents.grounding import ground_check
from app.agents.tools import parse_tool_call, keyword_fallback, RunPlanTool, MarginalTool
from app.agents.evidence_agent import generate_school_note, _template_school_note
from app.agents.tradeoff_agent import generate_item_rationale, _template_item_rationale


# ── Grounding tests ──────────────────────────────────────────────────────────

def test_grounding_passes_no_numbers():
    passed, msg = ground_check("The school has no electricity.", {"school": "test"})
    assert passed

def test_grounding_passes_known_number():
    passed, msg = ground_check(
        "The budget is 5000000.",
        {"budget": 5000000}
    )
    assert passed

def test_grounding_fails_hallucinated_large_number():
    passed, msg = ground_check(
        "The school needs Rs. 9999999 for repairs.",
        {"budget": 5000000, "cost": 400000}
    )
    assert not passed

def test_grounding_allows_small_counts():
    passed, msg = ground_check(
        "There are 3 schools with confirmed gaps.",
        {}
    )
    assert passed  # small numbers < 1000 are allowed freely


# ── Tool call parsing ────────────────────────────────────────────────────────

def test_parse_valid_run_plan():
    raw = '{"tool": "run_plan", "budget": 5000000}'
    tool = parse_tool_call(raw)
    assert tool is not None
    assert tool.tool == "run_plan"
    assert tool.budget == 5000000

def test_parse_valid_compare():
    raw = '{"tool": "compare_scenarios", "budget": 3000000}'
    tool = parse_tool_call(raw)
    assert tool is not None
    assert tool.tool == "compare_scenarios"

def test_parse_invalid_json_returns_none():
    tool = parse_tool_call("not json at all")
    assert tool is None

def test_parse_unknown_tool_returns_none():
    raw = '{"tool": "delete_database", "budget": 1000}'
    tool = parse_tool_call(raw)
    assert tool is None

def test_parse_budget_clamped():
    # Budget below minimum should be clamped
    raw = '{"tool": "run_plan", "budget": 1}'
    tool = parse_tool_call(raw)
    # pydantic field_validator with ge=100000 raises error for values below min
    assert tool is None or tool.budget >= 100000

def test_keyword_fallback_marginal():
    tool = keyword_fallback("what does the next budget fund", 5000000)
    assert tool is not None
    assert tool.tool == "marginal"

def test_keyword_fallback_lakh():
    tool = keyword_fallback("set budget to 30 lakh", 5000000)
    assert tool is not None
    assert tool.tool == "run_plan"
    assert tool.budget == pytest.approx(3000000)

def test_keyword_fallback_compare():
    tool = keyword_fallback("compare scenarios", 5000000)
    assert tool is not None
    assert tool.tool == "compare_scenarios"

def test_keyword_fallback_drop_percent():
    tool = keyword_fallback("drop budget by 30%", 5000000)
    assert tool is not None


# ── Evidence agent templates ─────────────────────────────────────────────────

def test_template_school_note_has_gaps():
    note = _template_school_note(
        "School 123",
        {"electricity": "CONFIRMED_GAP", "library": "CONFIRMED_OK", "computers": "CONFIRMED_GAP"},
        {"electricity": "ELIGIBLE", "library": "NOT_ELIGIBLE", "computers": "ELIGIBLE"},
    )
    assert "electricity" in note
    assert "computers" in note

def test_template_school_note_blocked():
    note = _template_school_note(
        "School 456",
        {"electricity": "MISSING", "library": "CONFIRMED_OK", "computers": "CONFIRMED_GAP"},
        {"electricity": "NOT_ELIGIBLE", "library": "NOT_ELIGIBLE", "computers": "BLOCKED_PREREQ_UNVERIFIED"},
    )
    assert "blocked" in note.lower() or "electricity" in note.lower()

def test_evidence_agent_fallback_no_granite():
    """With Granite unavailable, should return template."""
    with patch("app.agents.evidence_agent.call_granite", return_value=("", "template")):
        note, source = generate_school_note(
            "Test School",
            "04",
            {"electricity": "CONFIRMED_GAP", "library": "CONFIRMED_OK", "computers": "MISSING"},
            {"electricity": "ELIGIBLE", "library": "NOT_ELIGIBLE", "computers": "BLOCKED_PREREQ_UNVERIFIED"},
        )
    assert source == "template"
    assert len(note) > 10

def test_evidence_agent_rejects_hallucinated_number():
    """Grounding check should reject Granite output with invented numbers."""
    with patch("app.agents.evidence_agent.call_granite", return_value=("The school needs Rs. 9999999.", "granite")):
        note, source = generate_school_note(
            "Test School", "04",
            {"electricity": "CONFIRMED_GAP"},
            {"electricity": "ELIGIBLE"},
        )
    assert source == "template"


# ── Trade-off agent templates ────────────────────────────────────────────────

def test_template_item_funded():
    item = {"school_name": "School A", "facility": "electricity", "cost": 250000, "priority": 1.0, "status": "selected"}
    note = _template_item_rationale(item, 250000, 5000000)
    assert "electricity" in note.lower()
    assert "funded" in note.lower() or "provision" in note.lower()

def test_template_item_deferred():
    item = {"school_name": "School B", "facility": "computers", "cost": 400000, "priority": 0.9,
            "status": "deferred", "reason_code": "OUT_OF_BUDGET"}
    note = _template_item_rationale(item, 4900000, 5000000)
    assert "deferred" in note.lower()

def test_tradeoff_agent_fallback():
    item = {"school_name": "School C", "facility": "library", "cost": 150000,
            "priority": 0.8, "status": "selected", "reason_code": ""}
    with patch("app.agents.tradeoff_agent.call_granite", return_value=("", "template")):
        note, source = generate_item_rationale(item, 150000, 5000000)
    assert source == "template"
    assert len(note) > 10
