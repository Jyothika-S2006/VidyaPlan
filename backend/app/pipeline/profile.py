"""Data profiler: generates DATA_PROFILE.md from the raw CSV."""
import csv
import collections
from pathlib import Path

BASE = Path(__file__).parent.parent.parent.parent
DATA_RAW = BASE / "data" / "raw"
OUTPUT = BASE / "data" / "DATA_PROFILE.md"


def profile_csv() -> str:
    """Generate a Markdown profile of the raw CSV."""
    csv_files = list(DATA_RAW.glob("*.csv"))
    if not csv_files:
        return "No CSV files found in data/raw/"

    csv_file = csv_files[0]
    with open(csv_file, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        return "CSV is empty."

    columns = list(rows[0].keys())
    n = len(rows)
    lines = [
        "# Data Profile — Karnataka Schools Facilities 2017-18",
        "",
        f"**Source file:** `{csv_file.name}`",
        f"**Row count:** {n:,}",
        f"**Column count:** {len(columns)}",
        "",
        "## Column Summary",
        "",
        "| Column | Null % | Unique | Sample Values |",
        "|--------|--------|--------|---------------|",
    ]

    for col in columns:
        values = [r.get(col, "") for r in rows]
        blanks = sum(1 for v in values if v == "" or v is None)
        null_pct = round(blanks / n * 100, 1)
        unique_vals = set(values)
        n_unique = len(unique_vals)
        # Show distribution for low-cardinality columns
        if n_unique <= 15:
            counts = collections.Counter(values)
            sample = ", ".join(f"{k}:{v}" for k, v in sorted(counts.items())[:8])
        else:
            sample = f"{n_unique} unique values"
        lines.append(f"| `{col}` | {null_pct}% | {n_unique} | {sample} |")

    lines += [
        "",
        "## Column Mapping (confirmed)",
        "",
        "| Canonical Field | CSV Column | Notes |",
        "|---|---|---|",
        "| school_id | SCHCD | 11-digit code |",
        "| observation_year | AC_YEAR | 2017-18 for all rows |",
        "| electricity | ELECTRIC_YN | 1=OK, 2=GAP, 3=UNRELIABLE, 9=MISSING |",
        "| library | LIBRARY_YN | 1=OK, 2=GAP, 9=MISSING |",
        "| computers | COMPUTER | count: 0=GAP, >=1=OK |",
        "| district | derived | SCHCD[2:4] |",
        "| block | derived | SCHCD[4:6] |",
        "| school_name | derived | No name column in dataset |",
        "| enrollment | — | No enrollment column; need_multiplier=1.0 |",
        "",
        "## Data Quality Observations",
        "",
        "- **BLDSTATUS=9**: School has no building — all facility data treated as MISSING.",
        "- **ELECTRIC_YN=3**: Partial/unclear electricity — classified UNRELIABLE.",
        "- **ELECTRIC_YN=9 / LIBRARY_YN=9**: No data recorded — classified MISSING.",
        "- **COMPUTER field**: Numeric count, not Yes/No. Requires special handling.",
        "- **No school name column**: Name derived from SCHCD code.",
        "- **No enrollment column**: need_multiplier defaults to 1.0 for all schools.",
    ]
    return "\n".join(lines)


def main():
    profile = profile_csv()
    OUTPUT.write_text(profile, encoding="utf-8")
    print(f"Profile written to {OUTPUT}")


if __name__ == "__main__":
    main()
