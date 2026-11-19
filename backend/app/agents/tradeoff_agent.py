"""Trade-off Explanation Agent.

Takes a facts JSON (selected items, deferred items, reason codes, scenario diffs)
and generates:
- A per-item rationale for each funded and deferred recommendation.
- A scenario comparison narrative when scenario diffs are provided.

All outputs are grounding-checked. Falls back to template on any failure.
"""
import hashlib
import logging
from pathlib import Path

from app.agents.grounding import ground_check
from app.agents.granite_client import call_granite

logger = logging.getLogger(__name__)
PROMPTS_DIR = Path(__file__).parent / "prompts"

_cache: dict[str, tuple[str, str]] = {}


def _hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def _load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _template_item_rationale(item: dict, budget_used: float, total_budget: float) -> str:
    """Template explanation for a funded or deferred item."""
    name = item.get("school_name", f"School {item.get('school_id', '?')}")
    facility = item.get("facility", "facility")
    cost = item.get("cost", 0)
    decision = item.get("status", "selected")
    reason = item.get("reason_code", "")

    if decision == "selected":
        return (
            f"{facility.capitalize()} provision at {name} was funded "
            f"(cost Rs. {int(cost):,}, priority score {item.get('priority', 0):.2f}). "
            f"This represents a confirmed gap with supporting evidence from 2017-18 records."
        )
    else:
        reason_text = {
            "OUT_OF_BUDGET": "the remaining budget was insufficient",
            "LOWER_PRIORITY_PER_RUPEE": "higher-priority items consumed the available budget",
            "BLOCKED_PREREQ_UNVERIFIED": "electricity status is unverified, blocking computer provision",
            "DATA_MISSING": "data for this facility is missing",
            "UNRELIABLE_FIELD_EXCLUDED": "the field data is unreliable",
            "NOT_A_GAP": "no confirmed gap exists for this facility",
        }.get(reason, reason or "budget constraints")
        return (
            f"{facility.capitalize()} provision at {name} was deferred because {reason_text} "
            f"(cost would have been Rs. {int(cost):,})."
        )


def generate_item_rationale(
    item: dict,
    budget_used: float,
    total_budget: float,
) -> tuple[str, str]:
    """
    Generate a 1-2 sentence rationale for a recommendation item.

    Returns:
        (rationale_text, source) where source is "granite" or "template".
    """
    template = _template_item_rationale(item, budget_used, total_budget)
    facts = {
        "school_name": item.get("school_name", ""),
        "facility": item.get("facility", ""),
        "cost": item.get("cost", 0),
        "priority": item.get("priority", 0),
        "status": item.get("status", "selected"),
        "reason_code": item.get("reason_code", ""),
        "budget_used": budget_used,
        "total_budget": total_budget,
    }

    prompt_tpl = _load_prompt("tradeoff_item.txt")
    if not prompt_tpl:
        return template, "template"

    prompt = prompt_tpl.format(
        school_name=facts["school_name"],
        facility=facts["facility"],
        cost=int(facts["cost"]),
        priority=round(facts["priority"], 2),
        decision=facts["status"],
        reason_code=facts["reason_code"] or "N/A",
        budget_used=int(budget_used),
        total_budget=int(total_budget),
    )

    key = _hash(prompt)
    if key in _cache:
        return _cache[key]

    text, source = call_granite(prompt, max_tokens=128)
    if not text or source == "template":
        return template, "template"

    passed, _ = ground_check(text, facts)
    if not passed:
        logger.warning("Grounding failed for item rationale; using template.")
        return template, "template"

    _cache[key] = (text.strip(), "granite")
    return text.strip(), "granite"


def generate_batch_rationales(
    selected: list[dict],
    deferred: list[dict],
    budget_used: float,
    total_budget: float,
) -> list[dict]:
    """
    Generate rationales for all selected and deferred items.

    Returns:
        List of dicts with item data + explanation + explanation_source.
    """
    results = []
    for item in selected:
        text, source = generate_item_rationale(item, budget_used, total_budget)
        results.append({**item, "explanation": text, "explanation_source": source})
    for item in deferred:
        text, source = generate_item_rationale(item, budget_used, total_budget)
        results.append({**item, "explanation": text, "explanation_source": source})
    return results
