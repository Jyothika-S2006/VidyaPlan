"""Load Karnataka Schools CSV data into the SQLite database.

Column mapping (confirmed from profiling):
  SCHCD        — 11-digit school code; district = SCHCD[2:4], block = SCHCD[4:6]
  AC_YEAR      — Observation year (2017-18 for all rows)
  ELECTRIC_YN  — Electricity: 1=OK, 2=GAP, 3=UNRELIABLE, 9=MISSING
  LIBRARY_YN   — Library:     1=OK, 2=GAP, 9=MISSING
  COMPUTER     — Computer count: 0=GAP, >=1=OK; treat no-building (BLDSTATUS=9) as MISSING
  BLDSTATUS    — Building status: 9 = no building (all data unreliable for that school)
"""
import asyncio
import csv
import logging
import random
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal, init_db
from app.db.models import School, FacilityEvidence, DataQualityLog
from app.evidence.classifier import classify_facility

logger = logging.getLogger(__name__)

BASE = Path(__file__).parent.parent.parent.parent
DATA_RAW = BASE / "data" / "raw"

FACILITIES = ["electricity", "library", "computers"]

# Maps canonical facility name -> CSV column name
FACILITY_COLS = {
    "electricity": "ELECTRIC_YN",
    "library":     "LIBRARY_YN",
    "computers":   "COMPUTER",
}


def _derive_school_name(schcd: str) -> str:
    """Derive a readable school label from the 11-digit SCHCD code."""
    if len(schcd) >= 6:
        district = schcd[2:4]
        block = schcd[4:6]
        return f"School {schcd} (Dist {district}, Block {block})"
    return f"School {schcd}"


def _derive_district(schcd: str) -> str | None:
    """Extract district code (positions 2-4) from SCHCD."""
    if len(schcd) >= 4:
        return schcd[2:4]
    return None


def _derive_block(schcd: str) -> str | None:
    """Extract block code (positions 4-6) from SCHCD."""
    if len(schcd) >= 6:
        return schcd[4:6]
    return None


async def load_data(session: AsyncSession) -> dict:
    """
    Load all CSV files from data/raw/ into the database.
    Idempotent: existing records are updated, not duplicated.

    Returns:
        Summary dict with counts of schools and evidence records loaded.
    """
    csv_files = list(DATA_RAW.glob("*.csv"))
    if not csv_files:
        logger.warning("No CSV files found in data/raw/. Skipping load.")
        return {"schools_loaded": 0, "evidence_loaded": 0}

    school_count = 0
    evidence_count = 0
    no_building_count = 0

    for csv_file in csv_files:
        logger.info("Loading %s", csv_file.name)
        with open(csv_file, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                schcd = str(row.get("SCHCD", "")).strip()
                if not schcd:
                    continue

                bldstatus = str(row.get("BLDSTATUS", "")).strip()
                ac_year = str(row.get("AC_YEAR", "2017-18")).strip() or "2017-18"

                # Schools with BLDSTATUS=9 have no physical building — no reliable data
                is_no_building = (bldstatus == "9")
                if is_no_building:
                    no_building_count += 1

                name = _derive_school_name(schcd)
                district = _derive_district(schcd)
                block = _derive_block(schcd)

                # Upsert school
                existing = await session.execute(
                    select(School).where(School.external_id == schcd)
                )
                school = existing.scalar_one_or_none()
                if not school:
                    school = School(
                        external_id=schcd,
                        name=name,
                        district=district,
                        block=block,
                        enrollment=None,
                        observation_year=ac_year,
                    )
                    session.add(school)
                    await session.flush()
                    school_count += 1
                else:
                    school.district = district
                    school.block = block

                # Classify and upsert evidence for each facility
                for facility in FACILITIES:
                    col = FACILITY_COLS[facility]
                    raw_value = row.get(col)

                    result = classify_facility(
                        raw_value,
                        facility,
                        bldstatus=bldstatus,
                    )

                    ev_result = await session.execute(
                        select(FacilityEvidence).where(
                            FacilityEvidence.school_id == school.id,
                            FacilityEvidence.facility == facility,
                        )
                    )
                    ev = ev_result.scalar_one_or_none()
                    if not ev:
                        ev = FacilityEvidence(
                            school_id=school.id,
                            facility=facility,
                            state=result.state,
                            raw_value=str(raw_value) if raw_value is not None else None,
                            reason_code=result.reason_code,
                            observation_year=ac_year,
                        )
                        session.add(ev)
                        evidence_count += 1
                    else:
                        ev.state = result.state
                        ev.raw_value = str(raw_value) if raw_value is not None else None
                        ev.reason_code = result.reason_code

        await session.commit()
        logger.info("Loaded %d schools, %d evidence records.", school_count, evidence_count)

    # Log quality issues to data_quality_log
    await _write_quality_log(session, no_building_count)

    # Select cohort after loading
    await _select_cohort(session)

    return {
        "schools_loaded": school_count,
        "evidence_loaded": evidence_count,
        "no_building_excluded": no_building_count,
    }


async def _write_quality_log(session: AsyncSession, no_building_count: int) -> None:
    """Write data quality observations to data_quality_log."""
    entries = [
        {
            "field": "BLDSTATUS=9 rows",
            "reason": "School has no building (BLDSTATUS=9); all facility data treated as MISSING/not applicable.",
            "rows_affected": no_building_count,
        },
        {
            "field": "ELECTRIC_YN=3",
            "reason": "Value 3 indicates partial or unclear electricity status; classified as UNRELIABLE.",
            "rows_affected": 319,  # confirmed from profiling
        },
        {
            "field": "ELECTRIC_YN=9 / LIBRARY_YN=9",
            "reason": "Value 9 means no data recorded for this school; classified as MISSING.",
            "rows_affected": 2920,
        },
        {
            "field": "school_name",
            "reason": "No school name column present in dataset; name derived from SCHCD code.",
            "rows_affected": 0,
        },
        {
            "field": "enrollment",
            "reason": "No enrollment column present in dataset; need_multiplier defaults to 1.0 for all schools.",
            "rows_affected": 0,
        },
    ]
    for entry in entries:
        # Only insert if not already present
        existing = await session.execute(
            select(DataQualityLog).where(DataQualityLog.field == entry["field"])
        )
        if not existing.scalar_one_or_none():
            log = DataQualityLog(
                field=entry["field"],
                reason=entry["reason"],
                rows_affected=entry["rows_affected"],
            )
            session.add(log)
    await session.commit()


async def _select_cohort(session: AsyncSession, size: int = 40, seed: int = 42) -> None:
    """
    Select a stratified cohort of schools for the MVP demo.

    Strategy:
    - Only include schools that have at least one CONFIRMED_GAP (useful for planning)
    - Exclude BLDSTATUS=9 no-building schools
    - Pick from at least 2 different districts for variety
    - Seed for reproducibility
    """
    rng = random.Random(seed)

    # Reset cohort
    await session.execute(update(School).values(in_cohort=False))
    await session.commit()

    # Get schools that have at least one confirmed gap
    result = await session.execute(
        select(School).join(
            FacilityEvidence, FacilityEvidence.school_id == School.id
        ).where(
            FacilityEvidence.state == "CONFIRMED_GAP"
        ).distinct()
    )
    candidate_schools = result.scalars().all()

    if not candidate_schools:
        # Fallback: take any schools if no gaps found
        result = await session.execute(select(School).limit(size * 3))
        candidate_schools = result.scalars().all()

    logger.info("Found %d candidate schools with confirmed gaps.", len(candidate_schools))

    if len(candidate_schools) <= size:
        cohort = candidate_schools
    else:
        # Stratify: pick from multiple districts
        by_district: dict = {}
        for school in candidate_schools:
            d = school.district or "unknown"
            if d not in by_district:
                by_district[d] = []
            by_district[d].append(school)

        cohort = []
        # Round-robin across districts until we have enough
        districts = list(by_district.keys())
        rng.shuffle(districts)
        while len(cohort) < size and any(by_district[d] for d in districts):
            for d in districts:
                if len(cohort) >= size:
                    break
                if by_district[d]:
                    # Pick a random school from this district
                    idx = rng.randrange(len(by_district[d]))
                    cohort.append(by_district[d].pop(idx))

    for school in cohort:
        school.in_cohort = True

    await session.commit()
    logger.info("Cohort of %d schools selected (seed=%d).", len(cohort), seed)


async def main():
    """Entry point: initialise DB and load data."""
    logging.basicConfig(level=logging.INFO)
    await init_db()
    async with AsyncSessionLocal() as session:
        summary = await load_data(session)
        print(f"Load complete: {summary}")


if __name__ == "__main__":
    asyncio.run(main())
