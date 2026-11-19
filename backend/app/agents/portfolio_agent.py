"""Portfolio Planning Agent.

Takes a natural-language instruction and:
1. Calls Granite to produce a JSON tool call.
2. Validates the tool call against the allowed schema.
3. Executes the solver tool.
4. Returns the result with the parsed tool call shown to the user.

Falls back to keyword parser if Granite fails or returns invalid JSON.
"""
import logging
from pathlib import Path

from app.agents.tools import parse_tool_call, keyword_fallback, ToolCall
from app.agents.granite_client import call_granite

logger = logging.getLogger(__name__)
PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8") if path.exists() else ""


def parse_instruction(instruction: str, default_budget: float) -> tuple[ToolCall | None, str]:
    """
    Parse a natural-language instruction into a validated tool call.

    Returns:
        (tool_call, source) where source is "granite" | "keyword" | "failed".
    """
    prompt_tpl = _load_prompt("portfolio_tool.txt")
    if prompt_tpl:
        # Use simple replace instead of .format() — the template contains JSON
        # literal braces that would cause KeyError with str.format().
        prompt = (
            prompt_tpl
            .replace("{default_budget}", str(int(default_budget)))
            .replace("{instruction}", instruction)
        )
        raw, source = call_granite(prompt, max_tokens=128, temperature=0.0)
        if raw and source == "granite":
            tool = parse_tool_call(raw)
            if tool:
                return tool, "granite"
            logger.warning("Granite returned unparseable tool call; trying keyword fallback.")

    # Keyword fallback
    tool = keyword_fallback(instruction, default_budget)
    if tool:
        return tool, "keyword"

    return None, "failed"


async def run_copilot(
    instruction: str,
    eligible_items: list[dict],
    budget: float,
) -> dict:
    """
    Execute a natural-language copilot request.

    Returns:
        dict with keys: tool_call (the parsed instruction), result, source.
    """
    from app.solver.model import solve
    from app.solver.scenarios import compare_scenarios, marginal_view

    tool, source = parse_instruction(instruction, budget)
    if tool is None:
        return {
            "status": "failed",
            "message": "Could not parse instruction. Please use the sliders instead.",
            "source": "failed",
            "tool_call": None,
            "result": None,
        }

    tool_name = tool.tool
    result_data: dict = {}

    if tool_name == "run_plan":
        result_data = solve(eligible_items, tool.budget)
    elif tool_name == "compare_scenarios":
        cmp = compare_scenarios(eligible_items, tool.budget)
        result_data = {
            "base": {"budget": cmp.base.budget, "funded": cmp.base.interventions_funded, "objective": cmp.base.objective},
            "low": {"budget": cmp.low.budget, "funded": cmp.low.interventions_funded, "objective": cmp.low.objective},
            "high": {"budget": cmp.high.budget, "funded": cmp.high.interventions_funded, "objective": cmp.high.objective},
            "gained_in_high": len(cmp.gained_in_high),
            "lost_in_low": len(cmp.lost_in_low),
        }
    elif tool_name == "marginal":
        mv = marginal_view(eligible_items, tool.budget, getattr(tool, "extra_budget", 1_000_000))
        result_data = {
            "new_items": mv.new_items,
            "delta_interventions": mv.delta_interventions,
            "delta_schools": mv.delta_schools,
        }

    return {
        "status": "ok",
        "source": source,
        "tool_call": tool.model_dump(),
        "result": result_data,
        "provenance": "SIMULATED",
    }
