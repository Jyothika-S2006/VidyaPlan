"""Portfolio agent tool definitions and validators.

Allowed tool calls from Granite:
  run_plan(budget, weight_overrides?, exclude_types?)
  compare_scenarios(budget)
  marginal(budget, extra_budget?)

Validation uses pydantic. Ranges are clamped to safe values.
Keyword fallback parser handles common phrases.
"""
import logging
import json
import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

BUDGET_MIN = 100_000       # Rs. 1 lakh
BUDGET_MAX = 500_000_000   # Rs. 50 crore


class RunPlanTool(BaseModel):
    tool: str = "run_plan"
    budget: float = Field(..., ge=BUDGET_MIN, le=BUDGET_MAX)
    weight_overrides: Optional[dict] = None
    exclude_types: Optional[list[str]] = None

    @field_validator("budget")
    @classmethod
    def clamp_budget(cls, v: float) -> float:
        return max(BUDGET_MIN, min(BUDGET_MAX, v))


class CompareScenariosTool(BaseModel):
    tool: str = "compare_scenarios"
    budget: float = Field(..., ge=BUDGET_MIN, le=BUDGET_MAX)

    @field_validator("budget")
    @classmethod
    def clamp_budget(cls, v: float) -> float:
        return max(BUDGET_MIN, min(BUDGET_MAX, v))


class MarginalTool(BaseModel):
    tool: str = "marginal"
    budget: float = Field(..., ge=BUDGET_MIN, le=BUDGET_MAX)
    extra_budget: float = Field(default=1_000_000, ge=10_000, le=50_000_000)


ToolCall = RunPlanTool | CompareScenariosTool | MarginalTool


def parse_tool_call(raw: str) -> ToolCall | None:
    """
    Parse and validate a JSON tool call from Granite's output.

    Returns:
        A validated ToolCall, or None if parsing fails.
    """
    # Extract JSON from the response (Granite may add surrounding text)
    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
    if not json_match:
        return None
    try:
        data = json.loads(json_match.group(0))
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON from Granite response: %s", raw[:200])
        return None

    tool = data.get("tool", "")
    try:
        if tool == "run_plan":
            return RunPlanTool(**data)
        if tool == "compare_scenarios":
            return CompareScenariosTool(**data)
        if tool == "marginal":
            return MarginalTool(**data)
    except Exception as exc:
        logger.warning("Tool call validation failed: %s", exc)
    return None


def keyword_fallback(instruction: str, default_budget: float) -> ToolCall | None:
    """
    Keyword-based fallback parser for common instruction patterns.

    Examples:
      "drop budget 30%" -> compare_scenarios at 0.7 * budget
      "what if budget is 50 lakh" -> run_plan at 5000000
      "marginal" / "next 10 lakh" -> marginal
    """
    inst = instruction.lower()

    # Marginal view
    if "marginal" in inst or "next" in inst:
        return MarginalTool(tool="marginal", budget=default_budget)

    # Compare scenarios (budget drop/increase)
    if "drop" in inst or "compare" in inst or "scenario" in inst or "%" in inst:
        return CompareScenariosTool(tool="compare_scenarios", budget=default_budget)

    # Specific budget amount
    lakh_match = re.search(r'(\d+(?:\.\d+)?)\s*lakh', inst)
    crore_match = re.search(r'(\d+(?:\.\d+)?)\s*cr', inst)
    if lakh_match:
        budget = float(lakh_match.group(1)) * 100_000
        return RunPlanTool(tool="run_plan", budget=budget)
    if crore_match:
        budget = float(crore_match.group(1)) * 10_000_000
        return RunPlanTool(tool="run_plan", budget=budget)

    return None
