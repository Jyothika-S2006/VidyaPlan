"""Deterministic evidence classifier for facility gaps.

Evidence states:
  CONFIRMED_GAP  — facility confirmed absent; eligible for funding
  CONFIRMED_OK   — facility confirmed present
  MISSING        — no data recorded (field is 9 or blank)
  UNRELIABLE     — contradictory or uninterpretable value (e.g. partial electricity)

Rules are based on the confirmed column profiles from Karnataka Schools 2017-18:
  ELECTRIC_YN: 1=OK, 2=GAP, 3=UNRELIABLE, 9=MISSING
  LIBRARY_YN:  1=OK, 2=GAP, 9=MISSING
  COMPUTER:    numeric count — 0=GAP, >=1=OK; rows with BLDSTATUS=9 and 9 in COMPUTER=UNRELIABLE
"""
from typing import NamedTuple


class EvidenceResult(NamedTuple):
    """Result of classifying a single (school, facility) pair."""
    state: str       # CONFIRMED_GAP, CONFIRMED_OK, MISSING, UNRELIABLE
    reason_code: str


def classify_electricity(raw_value: str | None) -> EvidenceResult:
    """
    Classify ELECTRIC_YN field.
    1=Present(OK), 2=Absent(GAP), 3=Partial(UNRELIABLE), 9=No data(MISSING).
    """
    if raw_value is None or str(raw_value).strip() == "":
        return EvidenceResult("MISSING", "BLANK_FIELD")
    v = str(raw_value).strip()
    if v == "1":
        return EvidenceResult("CONFIRMED_OK", "RULE_MATCH")
    if v == "2":
        return EvidenceResult("CONFIRMED_GAP", "RULE_MATCH")
    if v == "3":
        return EvidenceResult("UNRELIABLE", "PARTIAL_OR_UNCLEAR")
    if v == "9":
        return EvidenceResult("MISSING", "NO_DATA_RECORDED")
    return EvidenceResult("UNRELIABLE", "UNRECOGNISED_VALUE")


def classify_library(raw_value: str | None) -> EvidenceResult:
    """
    Classify LIBRARY_YN field.
    1=Present(OK), 2=Absent(GAP), 9=No data(MISSING).
    """
    if raw_value is None or str(raw_value).strip() == "":
        return EvidenceResult("MISSING", "BLANK_FIELD")
    v = str(raw_value).strip()
    if v == "1":
        return EvidenceResult("CONFIRMED_OK", "RULE_MATCH")
    if v == "2":
        return EvidenceResult("CONFIRMED_GAP", "RULE_MATCH")
    if v == "9":
        return EvidenceResult("MISSING", "NO_DATA_RECORDED")
    return EvidenceResult("UNRELIABLE", "UNRECOGNISED_VALUE")


def classify_computers(raw_value: str | None, bldstatus: str | None = None) -> EvidenceResult:
    """
    Classify COMPUTER field (numeric count of computers).

    0 = CONFIRMED_GAP (no computers)
    >= 1 = CONFIRMED_OK (has computers)
    blank = MISSING
    Non-numeric or negative = UNRELIABLE

    Special: schools with BLDSTATUS=9 (no building) have no data; treat as MISSING.
    """
    if raw_value is None or str(raw_value).strip() == "":
        return EvidenceResult("MISSING", "BLANK_FIELD")

    # Schools with no building (BLDSTATUS=9) — all their data is unreliable
    if bldstatus is not None and str(bldstatus).strip() == "9":
        return EvidenceResult("MISSING", "NO_BUILDING_NO_DATA")

    v = str(raw_value).strip()
    try:
        count = int(float(v))
    except (ValueError, TypeError):
        return EvidenceResult("UNRELIABLE", "NON_NUMERIC_VALUE")

    if count < 0:
        return EvidenceResult("UNRELIABLE", "NEGATIVE_COUNT")
    if count == 0:
        return EvidenceResult("CONFIRMED_GAP", "ZERO_COMPUTERS")
    return EvidenceResult("CONFIRMED_OK", "HAS_COMPUTERS")


def classify_facility(raw_value: str | None, facility: str, bldstatus: str | None = None) -> EvidenceResult:
    """
    Dispatch to the correct classifier for the given facility.

    Args:
        raw_value: The raw string value from the CSV.
        facility: One of 'electricity', 'library', 'computers'.
        bldstatus: Raw BLDSTATUS value (used for computers to detect no-building schools).

    Returns:
        EvidenceResult with state and reason_code.
    """
    if facility == "electricity":
        return classify_electricity(raw_value)
    if facility == "library":
        return classify_library(raw_value)
    if facility == "computers":
        return classify_computers(raw_value, bldstatus)
    # Unknown facility — treat as missing
    return EvidenceResult("MISSING", f"UNKNOWN_FACILITY_{facility}")


def compute_eligibility(evidence: dict[str, str]) -> dict[str, str]:
    """
    Compute intervention eligibility for a school given its evidence states.

    Args:
        evidence: Dict mapping facility -> state for a single school.

    Returns:
        Dict mapping facility -> eligibility status.
    """
    eligibility = {}
    for facility in ["electricity", "library", "computers"]:
        state = evidence.get(facility, "MISSING")
        if facility == "computers":
            elec_state = evidence.get("electricity", "MISSING")
            if state == "CONFIRMED_GAP":
                if elec_state == "CONFIRMED_OK":
                    eligibility[facility] = "ELIGIBLE"
                elif elec_state == "CONFIRMED_GAP":
                    eligibility[facility] = "ELIGIBLE_IF_ELECTRICITY_FUNDED"
                else:
                    # electricity is MISSING or UNRELIABLE — computers blocked
                    eligibility[facility] = "BLOCKED_PREREQ_UNVERIFIED"
            else:
                eligibility[facility] = "NOT_ELIGIBLE"
        else:
            eligibility[facility] = "ELIGIBLE" if state == "CONFIRMED_GAP" else "NOT_ELIGIBLE"

    return eligibility
