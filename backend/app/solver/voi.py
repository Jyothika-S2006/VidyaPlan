"""Value of Information (VOI) — Verify-First Queue.

For each MISSING field f among the top candidates:
  VOI(f) = P(gap_f) * [OPT(confirmed + f treated as gap) - OPT(confirmed)]

Interpretation: if we verify field f and it turns out to be a gap,
the plan improves by [OPT(...+f) - OPT(...)]. The expected improvement
is P(gap_f) times that delta. If not a gap, nothing changes.

This is a heuristic — single-field VOI ignoring correlations.
Cap candidates to top ~60 by priority/cost to keep it fast.
Include BLOCKED_PREREQ_UNVERIFIED computers here (verifying electricity unlocks them).

All outputs labelled SIMULATED.
"""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VoiEntry:
    """A single entry in the Verify-First Queue."""
    school_id: int
    school_name: str
    facility: str
    district: str | None
    p_gap: float
    base_objective: float
    augmented_objective: float
    voi_rs: float            # expected value of perfect information in Rs equivalent (objective units * cost scale)
    action_text: str
    provenance: str = "SIMULATED"


def compute_voi(
    eligible_items: list[dict],
    missing_items: list[dict],
    blocked_items: list[dict],
    p_gap: dict[str, float],
    budget: float,
    base_objective: float,
    top_n: int = 10,
    candidate_cap: int = 60,
) -> list[VoiEntry]:
    """
    Compute VOI for the top candidate MISSING + BLOCKED fields.

    Args:
        eligible_items: items already eligible (CONFIRMED_GAP).
        missing_items: items from MISSING fields with school_id, facility,
                       cost, priority, electricity_state, school_name, district.
        blocked_items: BLOCKED_PREREQ_UNVERIFIED computer items.
        p_gap: dict mapping str(school_id) -> P(gap) for missing electricity.
        budget: total budget in Rs.
        base_objective: objective value of the base plan (confirmed gaps only).
        top_n: number of top VOI entries to return.
        candidate_cap: max candidates to evaluate (performance limit).

    Returns:
        List of VoiEntry sorted by voi_rs descending, limited to top_n.
    """
    from app.solver.model import solve

    # Rank candidates by priority/cost — only evaluate the top ones
    all_candidates = missing_items + blocked_items
    ranked = sorted(
        all_candidates,
        key=lambda x: x.get("priority", 0.8) / max(x.get("cost", 1), 1),
        reverse=True,
    )[:candidate_cap]

    entries: list[VoiEntry] = []

    for item in ranked:
        sid = str(item["school_id"])
        p = p_gap.get(sid, 0.3)
        if p <= 0:
            continue

        # Augmented solve: add this item as if it were a confirmed gap
        # For blocked items: also need to treat the electricity as confirmed OK
        augmented = eligible_items + [item]

        # If this is a blocked computer item, also add electricity as eligible
        if item.get("facility") == "computers" and item.get("electricity_state") in ("MISSING", "UNRELIABLE"):
            # Create a hypothetical electricity item for this school
            elec_item = {
                "id": f"{item['school_id']}_electricity_voi",
                "school_id": item["school_id"],
                "school_name": item.get("school_name", f"School {item['school_id']}"),
                "facility": "electricity",
                "cost": 250000,  # default cost
                "priority": 1.0,
                "electricity_state": "CONFIRMED_GAP",
            }
            augmented = eligible_items + [elec_item, item]

        result = solve(augmented, budget)
        aug_objective = result["objective"]

        delta = max(0.0, aug_objective - base_objective)
        voi = p * delta

        if voi <= 0:
            continue

        facility = item.get("facility", "")
        school_name = item.get("school_name", f"School {item['school_id']}")
        district = item.get("district")

        if facility == "computers":
            action_text = (
                f"Verify electricity at {school_name} to unlock computer provision "
                f"(VOI: Rs. {int(voi * 100000):,})"
            )
        else:
            action_text = (
                f"Verify {facility} at {school_name} — could improve plan "
                f"(VOI: Rs. {int(voi * 100000):,})"
            )

        entries.append(VoiEntry(
            school_id=item["school_id"],
            school_name=school_name,
            facility=facility,
            district=district,
            p_gap=round(p, 4),
            base_objective=round(base_objective, 4),
            augmented_objective=round(aug_objective, 4),
            voi_rs=round(voi * 100000, 0),  # scale to Rs.
            action_text=action_text,
        ))

    entries.sort(key=lambda e: e.voi_rs, reverse=True)
    return entries[:top_n]
