# Problem Statement 17 — School Infra Karnataka

## Inter-Institute IBM Bob Hackathon with IBM SkillsBuild

**Domain:** Education Infrastructure, Public Resource Planning and Optimisation

## The Challenge

School infrastructure records can help identify facility gaps, but limited budgets prevent all improvements from being funded. Develop a transparent planning system that prioritises documented infrastructure needs while accounting for missing data, intervention costs and dependencies, such as electricity requirements for computer facilities.

## Objective

Build an Agentic AI-powered planner that identifies verified facility gaps and recommends budget-feasible improvements. For the MVP, analyse 30-50 schools across three interventions: library provision, electricity enablement and computer provision. Use configurable costs, priority weights and a budget-constrained optimisation algorithm.

## Suggested AI Agents

- **Facility Evidence Agent**: Analyse school records and distinguish confirmed gaps from missing information.
- **Portfolio Planning Agent**: Allocate budgets using Python tools while enforcing costs and intervention dependencies.
- **Trade-off Explanation Agent**: Explain selected and deferred interventions and compare alternative budget scenarios.

## Expected Outcome

An interactive dashboard displaying infrastructure gaps, proposed interventions, estimated costs and budget utilisation. Compare allocation scenarios and test limited budgets, missing records and unmet prerequisites. Clearly distinguish simulated estimates from official figures and require human review before real-world decisions.

## Technology

IBM Bob + IBM Granite LLM + IBM Cloud + Python, HTML5, CSS3, JavaScript, MySQL.
(Team has permission to use React for the frontend.)

## Data

Karnataka Schools Facilities Data 2017-18, containing school identifiers and infrastructure fields such as electricity, libraries and computers.
