# VidyaPlan — PPT Outline (10 slides)

## Slide 1: Title
**Title:** VidyaPlan — Budget-Constrained Infrastructure Planner for Karnataka Schools
**Team:** [Team name]
**One-line pitch:** "We fund what the records prove, and tell you exactly what to verify next."
**Hackathon:** Inter-Institute IBM Bob Hackathon · Problem Statement 17

---

## Slide 2: The Problem
**Headline:** Limited budgets, incomplete records, hidden dependencies
- 2017-18 data: some fields blank, some unreliable, some contradictory
- 77,000+ Karnataka schools, only 40 in MVP scope
- Computers require electricity — but electricity status is often unrecorded
- Existing approach: "find gaps, run knapsack, show dashboard" — ignores uncertainty

---

## Slide 3: Our Insight
**Headline:** Missing data is the real problem — plan with uncertainty
- Don't impute, don't ignore: tag every field CONFIRMED_GAP / CONFIRMED_OK / MISSING / UNRELIABLE
- Stress-test the plan against hundreds of possible completions of missing data
- Turn the missing-data problem into a decision: *which field visit improves the plan most?*

---

## Slide 4: Proposed Solution
**Headline:** 4-step agentic planner
1. **Data** — evidence classification, quality log, cohort selection
2. **Budget** — slider, configurable costs/weights, CP-SAT optimiser
3. **Plan** — funded interventions, stress-test, Verify-First Queue, scenario compare
4. **Review** — human approve/reject, audit log, PDF memo export

Three agents: **Evidence** (classify, explain) · **Portfolio** (NL → tool call → solver) · **Trade-off** (explain decisions)

---

## Slide 5: Architecture Diagram
[Insert mermaid diagram from docs/architecture.md]
- React frontend → FastAPI backend → OR-Tools solver + IBM Granite LLM → SQLite/MySQL
- IBM Cloud Code Engine hosting

---

## Slide 6: IBM Technology Usage
| Technology | How we use it |
|---|---|
| IBM Bob | Built the entire application iteratively using Bob prompts from the playbook |
| IBM Granite (watsonx.ai) | Generates grounded plain-language explanations; never produces numbers |
| IBM Cloud (Code Engine) | Hosts the production container; min-scale 1 for no cold start during demo |
| watsonx.ai project | Model inference endpoint for Granite |

**Grounding check:** every Granite output is verified against the facts payload before display. Invented numbers are rejected and replaced with a deterministic template. The UI shows an "AI / Template" chip.

---

## Slide 7: Our Differentiators
**What sets VidyaPlan apart from a standard knapsack tool:**

1. **Plan Stress-Test** — Monte Carlo (300 scenarios). Each funded pick gets a robustness score. Expected regret quantifies how much better we could do with full information.

2. **Verify-First Queue** — Value of Information ranking. "Verifying electricity at School X could improve the plan by Rs. Y." Missing data becomes an actionable field-visit priority list.

3. **Grounded AI** — Granite never produces numbers. Every figure is passed as facts; a grounding check rejects hallucinations. Template fallback = demo never breaks.

---

## Slide 8: IBM Cloud Implementation
[Screenshots of:]
- Code Engine app page with public URL
- Running health check at /health
- watsonx.ai project with Granite model
- Container registry (or local docker-compose for demo)

---

## Slide 9: Demo Screenshots
[Screenshots of:]
- Data page: KPI tiles + evidence breakdown
- Plan page: funded table + stress-test panel
- Plan page: Verify-First Queue
- Review page: approve/reject flow
- PDF memo (DRAFT watermark visible)

[Link to 3-minute recorded demo video]

---

## Slide 10: Impact and Scalability
**Measurable impact (real numbers from the solver):**
- Cohort: 40 schools, Rs. 50L budget → 14 interventions funded across 12 schools
- Baseline comparison: optimiser vs greedy vs random (shown in dashboard — honest numbers)

**Scalability:**
- Config-driven: any state, any intervention type, any budget — change config/*.yaml
- Full 77,000-school dataset already loaded; toggle in UI
- Solver runs in milliseconds; stress-test in seconds

**Limitations (honest):**
- 2017-18 data only — may not reflect current status
- Costs and weights are SIMULATED hypothetical values
- VOI is a single-field heuristic (ignores field correlations)
- Human review required before any real-world commitment

**Responsible AI:** Granite never produces numbers. Human approval required. All figures labelled OFFICIAL or SIMULATED.
