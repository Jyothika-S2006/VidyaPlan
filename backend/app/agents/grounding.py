"""Grounding check: verify generated text does not contain invented numbers."""
import re
import logging

logger = logging.getLogger(__name__)


def ground_check(text: str, facts: dict) -> tuple[bool, str]:
    """
    Check that every number in text exists in the facts payload.

    Returns:
        (passed: bool, message: str)
    """
    # Extract numbers from generated text
    numbers_in_text = set(re.findall(r'\b\d[\d,]*(?:\.\d+)?\b', text))

    # Build set of allowed numbers from facts (convert to string forms)
    allowed_numbers = set()
    _extract_numbers_from_facts(facts, allowed_numbers)

    # Check each number found in text
    for num in numbers_in_text:
        # Normalise: remove commas
        normalised = num.replace(",", "")
        # Allow small numbers (counts, percentages, years) freely
        try:
            val = float(normalised)
            if val < 1000 and val == int(val):
                continue  # counts, years, small numbers are allowed
        except ValueError:
            continue
        if normalised not in allowed_numbers:
            logger.warning("Grounding check failed: number %s not in facts", num)
            return False, f"Number {num} not found in facts"

    return True, "ok"


def _extract_numbers_from_facts(obj, result: set, depth: int = 0):
    """Recursively extract number strings from a nested dict/list."""
    if depth > 5:
        return
    if isinstance(obj, dict):
        for v in obj.values():
            _extract_numbers_from_facts(v, result, depth + 1)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            _extract_numbers_from_facts(item, result, depth + 1)
    elif isinstance(obj, (int, float)):
        result.add(str(int(obj)) if obj == int(obj) else str(obj))
        result.add(str(obj))
