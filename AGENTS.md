# VidyaPlan - Agent Context

You are the lead engineer building VidyaPlan for the Inter-Institute IBM Bob Hackathon, Problem Statement 17.

## Project
VidyaPlan is an uncertainty-aware, budget-constrained infrastructure planner for Karnataka schools.

## Stack
- Backend: Python 3.11 + FastAPI, SQLAlchemy 2 + SQLite (local dev), OR-Tools CP-SAT
- LLM: IBM watsonx.ai Granite via ibm-watsonx-ai SDK
- Frontend: React + Vite + TypeScript, pastel design system
- Hosting: IBM Cloud Code Engine

## Non-negotiable Rules
1. LLM never computes or invents numbers. Numbers come from DB or solver; Granite only explains.
2. Every figure carries a provenance label: OFFICIAL (2017-18 dataset) or SIMULATED.
3. Only CONFIRMED gaps are funded in the base plan. MISSING/UNRELIABLE are tagged, excluded, logged.
4. Dependency: computers require electricity.
5. Every watsonx call has timeout, retry, cache and deterministic template fallback.
6. Human must approve before plan is FINAL. All state changes go to append-only audit_log.
7. Config, not constants: costs, weights, rules, column mapping live in config/*.yaml.
8. Code quality: type hints, docstrings, small functions, pytest tests for all logic.
