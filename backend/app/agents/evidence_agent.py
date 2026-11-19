"""Facility Evidence Agent.

Runs the deterministic classifier, then calls Granite (with grounding check
and template fallback) to generate:
  (a) A 1-2 sentence plain-language evidence note per school.
  (b) A district-level data-quality summary.

Rules (non-negotiable):
- Rules decide; Granite only phrases.
- Every generated output is grounding-checked against the facts passed in.
- If Granite fails or grounding fails, return a template note.
- Cache by input hash to avoid repeat calls.
- Mark each output with source = "granite" | "template".

Performance note: Granite is only attempted for the first GRANITE_SCHOOL_CAP
schools per pipeline run. All others use deterministic templates immediately.
This avoids rate-limiting and keeps the pipeline fast for demos.
"""
import hashlib
import logging
from pathlib import Path

from app.agents.grounding import ground_check
from app.agents.granite_client import call_granite

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
GRANITE_SCHOOL_CAP = 0   # pipeline always uses templates (grounding fails on numeric IDs)

_cache: dict[str, tuple[str, str]] = {}  # hash -> (text, source)
_granite_calls_this_run: int = 0  # reset by orchestrator between runs


def _hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def _load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _template_school_note(school_name: str, evidence: dict, eligibility: dict) -> str:
    """Deterministic template note for a school."""
    gaps = [f for f, s in evidence.items() if s == "CONFIRMED_GAP"]
    missing = [f for f, s in evidence.items() if s == "MISSING"]
    blocked = [f for f, e in eligibility.items() if e == "BLOCKED_PREREQ_UNVERIFIED"]

    parts = []
    if gaps:
        parts.append(f"{school_name} has confirmed gaps in: {', '.join(gaps)}.")
    else:
        parts.append(f"{school_name} has no confirmed facility gaps in this dataset.")
    if missing:
        parts.append(f"Records for {', '.join(missing)} are missing and require field verification.")
    if blocked:
        parts.append(
            f"Computer provision is blocked pending electricity verification at this school."
        )
    return " ".join(parts)


def _template_district_summary(district: str, stats: dict) -> str:
    """Deterministic template summary for a district."""
    return (
        f"District {district} has {stats.get('total', 0)} schools in the cohort. "
        f"Confirmed gaps: electricity {stats.get('elec_gaps', 0)}, "
        f"library {stats.get('library_gaps', 0)}, "
        f"computers {stats.get('computer_gaps', 0)}. "
        f"Missing records: electricity {stats.get('elec_missing', 0)}, "
        f"library {stats.get('library_missing', 0)}, "
        f"computers {stats.get('computer_missing', 0)}."
    )


def reset_granite_counter() -> None:
    """Reset per-run Granite call counter. Called by the orchestrator."""
    global _granite_calls_this_run
    _granite_calls_this_run = 0


def generate_school_note(
    school_name: str,
    district: str | None,
    evidence: dict[str, str],
    eligibility: dict[str, str],
) -> tuple[str, str]:
    """
    Generate a 1-2 sentence evidence note for one school.

    Returns:
        (note_text, source) where source is "granite" or "template".
    """
    global _granite_calls_this_run
    template = _template_school_note(school_name, evidence, eligibility)

    # Fast path: skip Granite if cap reached (keeps pipeline fast)
    if _granite_calls_this_run >= GRANITE_SCHOOL_CAP:
        return template, "template"

    # Build facts for grounding
    facts = {
        "school_name": school_name,
        "evidence": evidence,
        "eligibility": eligibility,
    }

    prompt_tpl = _load_prompt("evidence_school.txt")
    if not prompt_tpl:
        return template, "template"

    evidence_lines = "\n".join(f"  {k}: {v}" for k, v in evidence.items())
    eligibility_lines = "\n".join(f"  {k}: {v}" for k, v in eligibility.items())
    prompt = prompt_tpl.format(
        school_name=school_name,
        district=district or "Unknown",
        evidence_lines=evidence_lines,
        eligibility_lines=eligibility_lines,
    )

    cache_key = _hash(prompt)
    if cache_key in _cache:
        return _cache[cache_key]

    _granite_calls_this_run += 1
    text, source = call_granite(prompt, max_tokens=128)
    if not text or source == "template":
        return template, "template"

    passed, _ = ground_check(text, facts)
    if not passed:
        logger.warning("Grounding check failed for school note; using template.")
        return template, "template"

    _cache[cache_key] = (text.strip(), "granite")
    return text.strip(), "granite"


def generate_district_summary(district: str, stats: dict) -> tuple[str, str]:
    """
    Generate a 2-3 sentence data-quality summary for a district.

    Returns:
        (summary_text, source) where source is "granite" or "template".
    """
    template = _template_district_summary(district, stats)
    facts = {**stats, "district": district}

    prompt_tpl = _load_prompt("evidence_district.txt")
    if not prompt_tpl:
        return template, "template"

    prompt = prompt_tpl.format(
        district=district,
        total_schools=stats.get("total", 0),
        elec_gaps=stats.get("elec_gaps", 0),
        library_gaps=stats.get("library_gaps", 0),
        computer_gaps=stats.get("computer_gaps", 0),
        elec_missing=stats.get("elec_missing", 0),
        library_missing=stats.get("library_missing", 0),
        computer_missing=stats.get("computer_missing", 0),
    )

    cache_key = _hash(prompt)
    if cache_key in _cache:
        return _cache[cache_key]

    text, source = call_granite(prompt, max_tokens=192)
    if not text or source == "template":
        return template, "template"

    passed, _ = ground_check(text, facts)
    if not passed:
        return template, "template"

    _cache[cache_key] = (text.strip(), "granite")
    return text.strip(), "granite"
