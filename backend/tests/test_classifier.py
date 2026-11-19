"""Tests for the evidence classifier with real Karnataka Schools 2017-18 column rules."""
import pytest
from app.evidence.classifier import (
    classify_facility,
    classify_electricity,
    classify_library,
    classify_computers,
    compute_eligibility,
)


# ── ELECTRIC_YN tests ───────────────────────────────────────────────────────

def test_electricity_ok():
    assert classify_electricity("1").state == "CONFIRMED_OK"

def test_electricity_gap():
    assert classify_electricity("2").state == "CONFIRMED_GAP"

def test_electricity_unreliable():
    result = classify_electricity("3")
    assert result.state == "UNRELIABLE"
    assert result.reason_code == "PARTIAL_OR_UNCLEAR"

def test_electricity_missing_9():
    result = classify_electricity("9")
    assert result.state == "MISSING"
    assert result.reason_code == "NO_DATA_RECORDED"

def test_electricity_missing_blank():
    assert classify_electricity("").state == "MISSING"
    assert classify_electricity(None).state == "MISSING"


# ── LIBRARY_YN tests ─────────────────────────────────────────────────────────

def test_library_ok():
    assert classify_library("1").state == "CONFIRMED_OK"

def test_library_gap():
    assert classify_library("2").state == "CONFIRMED_GAP"

def test_library_missing_9():
    assert classify_library("9").state == "MISSING"

def test_library_missing_blank():
    assert classify_library("").state == "MISSING"
    assert classify_library(None).state == "MISSING"


# ── COMPUTER (count) tests ───────────────────────────────────────────────────

def test_computers_gap_zero():
    result = classify_computers("0")
    assert result.state == "CONFIRMED_GAP"
    assert result.reason_code == "ZERO_COMPUTERS"

def test_computers_ok_one():
    assert classify_computers("1").state == "CONFIRMED_OK"

def test_computers_ok_large():
    assert classify_computers("30").state == "CONFIRMED_OK"

def test_computers_missing_blank():
    assert classify_computers("").state == "MISSING"
    assert classify_computers(None).state == "MISSING"

def test_computers_no_building():
    """BLDSTATUS=9 means no building; treat as MISSING regardless of COMPUTER value."""
    result = classify_computers("0", bldstatus="9")
    assert result.state == "MISSING"
    assert result.reason_code == "NO_BUILDING_NO_DATA"

def test_computers_no_building_even_if_has_computers():
    result = classify_computers("5", bldstatus="9")
    assert result.state == "MISSING"


# ── dispatch via classify_facility ───────────────────────────────────────────

def test_dispatch_electricity():
    assert classify_facility("2", "electricity").state == "CONFIRMED_GAP"

def test_dispatch_library():
    assert classify_facility("2", "library").state == "CONFIRMED_GAP"

def test_dispatch_computers():
    assert classify_facility("0", "computers").state == "CONFIRMED_GAP"

def test_dispatch_computers_with_bldstatus():
    assert classify_facility("0", "computers", bldstatus="9").state == "MISSING"


# ── compute_eligibility tests ─────────────────────────────────────────────────

def test_computers_blocked_when_electricity_missing():
    evidence = {"electricity": "MISSING", "library": "CONFIRMED_GAP", "computers": "CONFIRMED_GAP"}
    eligibility = compute_eligibility(evidence)
    assert eligibility["computers"] == "BLOCKED_PREREQ_UNVERIFIED"

def test_computers_blocked_when_electricity_unreliable():
    evidence = {"electricity": "UNRELIABLE", "library": "CONFIRMED_OK", "computers": "CONFIRMED_GAP"}
    eligibility = compute_eligibility(evidence)
    assert eligibility["computers"] == "BLOCKED_PREREQ_UNVERIFIED"

def test_computers_eligible_when_electricity_ok():
    evidence = {"electricity": "CONFIRMED_OK", "library": "CONFIRMED_GAP", "computers": "CONFIRMED_GAP"}
    eligibility = compute_eligibility(evidence)
    assert eligibility["computers"] == "ELIGIBLE"

def test_computers_eligible_if_electricity_also_gap():
    evidence = {"electricity": "CONFIRMED_GAP", "library": "CONFIRMED_OK", "computers": "CONFIRMED_GAP"}
    eligibility = compute_eligibility(evidence)
    assert eligibility["computers"] == "ELIGIBLE_IF_ELECTRICITY_FUNDED"

def test_library_eligible_independent_of_electricity():
    evidence = {"electricity": "MISSING", "library": "CONFIRMED_GAP", "computers": "CONFIRMED_OK"}
    eligibility = compute_eligibility(evidence)
    assert eligibility["library"] == "ELIGIBLE"

def test_not_eligible_when_ok():
    evidence = {"electricity": "CONFIRMED_OK", "library": "CONFIRMED_OK", "computers": "CONFIRMED_OK"}
    eligibility = compute_eligibility(evidence)
    for f in ["electricity", "library", "computers"]:
        assert eligibility[f] == "NOT_ELIGIBLE"
