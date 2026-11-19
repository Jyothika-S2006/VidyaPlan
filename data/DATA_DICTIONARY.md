# Data Dictionary — VidyaPlan

## Source
Karnataka Schools Facilities Data 2017-18. All records from one academic year (2017-18).

## Canonical Fields

| Field | Source Column | Type | Description |
|---|---|---|---|
| school_id | SCHCD | string | 11-digit school code. Format: 29DDBBPPPSSS (DD=district, BB=block) |
| district | derived | string | SCHCD positions 2-4 (2-digit district code) |
| block | derived | string | SCHCD positions 4-6 (2-digit block code) |
| observation_year | AC_YEAR | string | Academic year of observation. All records: "2017-18" |
| electricity | ELECTRIC_YN | enum | Evidence state for electricity. See rules below. |
| library | LIBRARY_YN | enum | Evidence state for library. See rules below. |
| computers | COMPUTER | enum | Evidence state for computers. See rules below. |

## Evidence State Rules

### ELECTRIC_YN
| Raw Value | Evidence State | Reason Code |
|---|---|---|
| 1 | CONFIRMED_OK | RULE_MATCH |
| 2 | CONFIRMED_GAP | RULE_MATCH |
| 3 | UNRELIABLE | PARTIAL_OR_UNCLEAR |
| 9 | MISSING | NO_DATA_RECORDED |
| blank | MISSING | BLANK_FIELD |

### LIBRARY_YN
| Raw Value | Evidence State | Reason Code |
|---|---|---|
| 1 | CONFIRMED_OK | RULE_MATCH |
| 2 | CONFIRMED_GAP | RULE_MATCH |
| 9 | MISSING | NO_DATA_RECORDED |
| blank | MISSING | BLANK_FIELD |

### COMPUTER (numeric count)
| Raw Value | Evidence State | Reason Code |
|---|---|---|
| 0 | CONFIRMED_GAP | ZERO_COMPUTERS |
| >= 1 | CONFIRMED_OK | HAS_COMPUTERS |
| blank | MISSING | BLANK_FIELD |
| BLDSTATUS=9 | MISSING | NO_BUILDING_NO_DATA |

## Eligibility Rules

| Facility | Eligible When | Notes |
|---|---|---|
| electricity | CONFIRMED_GAP | — |
| library | CONFIRMED_GAP | — |
| computers | CONFIRMED_GAP AND electricity is CONFIRMED_OK | If electricity is also CONFIRMED_GAP, computers eligible only if electricity funded in same plan |
| computers | CONFIRMED_GAP AND electricity MISSING/UNRELIABLE | BLOCKED_PREREQ_UNVERIFIED — excluded from base plan, included in Verify-First queue |

## Intervention Defaults (all SIMULATED)

| Facility | Cost | Priority Weight |
|---|---|---|
| electricity | Rs. 2,50,000 | 1.0 |
| computers | Rs. 4,00,000 | 0.9 |
| library | Rs. 1,50,000 | 0.8 |

## Dropped / Excluded Fields

| Field | Reason |
|---|---|
| school_name | No name column in dataset |
| enrollment | No enrollment column; need_multiplier = 1.0 |
| BLDSTATUS=9 rows | No physical building — all facility data unreliable |
| ELECTRIC_YN=3 | Partial/unclear — not a confirmed gap, classified UNRELIABLE |
