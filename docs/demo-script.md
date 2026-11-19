# VidyaPlan — 3-Minute Demo Script

## Setup (before demo)
- Backend running: `uvicorn app.main:app --reload`
- Frontend running: `npm run dev`
- Browser open at `http://localhost:5173`
- DB already loaded with cohort (40 schools from 34 districts)

---

## 0:00 — Opening (20 sec)

**Say:** "Limited budgets, incomplete 2017-18 records. VidyaPlan funds only what the records prove — and tells you exactly which field visit would improve the plan most."

**Show:** The DataAsOfBanner at the top. Point to it: "This banner is always visible. Everything is 2017-18 official data."

---

## 0:20 — Data Step (25 sec)

**Navigate to:** Data page

**Say:** "77,000 Karnataka schools. We picked 40 for the MVP demo, stratified across districts."

**Show:** KPI tiles — 39 confirmed computer gaps, 1 electricity gap, 3 library gaps.

**Show:** Evidence breakdown — point to CONFIRMED_GAP vs MISSING vs UNRELIABLE.

**Show:** Data Quality Log — "BLDSTATUS=9 schools have no building; we exclude them, we never impute."

---

## 0:45 — Budget + Run Plan (35 sec)

**Navigate to:** Budget page

**Say:** "Rs. 50 lakh. The solver is OR-Tools CP-SAT — deterministic, milliseconds."

**Click:** Run Plan

**Navigate to:** Plan page

**Show:** 14 interventions funded at 94% budget utilisation.

**Point to:** Prerequisite-blocked list — "Computers at this school are blocked because we cannot confirm electricity. The dependency is enforced in the solver."

**Point to:** SIMULATED badges — "Every cost, weight and score is labelled."

---

## 1:20 — Stress-Test (30 sec)

**Click:** Run Stress-Test (100 scenarios)

**Say:** "Monte Carlo: 100 times, each MISSING field is randomly resolved. How many times does each funded pick survive?"

**Show:** Green picks (robust ≥ 85%), amber (60–85%), red (fragile < 60%).

**Say:** "Expected regret tells us: our plan is within X% of optimal with full information, on average."

---

## 1:50 — Verify-First Queue (25 sec)

**Click:** Compute VOI

**Say:** "Missing data is not a weakness — it's a decision tool. These are the field visits that would most improve the plan."

**Show:** Top entry — "Verifying electricity at School X unlocks computer provision."

**Say:** "VOI = P(it's a gap) × how much the plan improves if it is. Ranked by expected value."

---

## 2:15 — Scenario Compare or Copilot (25 sec)

**Option A — Copilot:** Type "what if budget drops 30%". Show parsed tool call, new plan.

**Option B — Scenario Compare:** Click Compare Scenarios. Show low/base/high side by side, gained/lost items highlighted.

**Say:** "The solver re-runs in milliseconds. The trade-off agent explains what was deferred and why."

---

## 2:40 — Review + Export (20 sec)

**Navigate to:** Review page

**Show:** Approve one recommendation with a note.

**Say:** "Nothing is FINAL until a human approves it. All decisions are recorded in the append-only audit log."

**Click:** Export Memo PDF — show the DRAFT watermark.

**Say:** "One click to a watermarked decision memo. Remove DRAFT only after full approval."

---

## Backup plan
- If Granite is unavailable: template fallback is shown with a "Template Explanation" chip — the demo never breaks.
- If Wi-Fi fails: local docker-compose and the recorded video.
- Demo preset button: pre-loads the fixed seed/budget plan for reproducibility.
