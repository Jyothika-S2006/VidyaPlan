"""IBM watsonx.ai Granite client with retry, cache and template fallback.

Uses the modern /ml/v1/text/chat API (ibm-watsonx-ai >= 1.0).
Falls back to deterministic templates on any failure.
Caches by MD5 of prompt to avoid repeat API calls.
"""
import hashlib
import logging
import time

logger = logging.getLogger(__name__)

_cache: dict = {}


class LlmUnavailable(Exception):
    """Raised when Granite is unreachable and no fallback is possible."""
    pass


def _get_cache_key(prompt: str) -> str:
    return hashlib.md5(prompt.encode()).hexdigest()


def call_granite(
    prompt: str,
    max_tokens: int = 256,
    temperature: float = 0.1,
    retries: int = 2,
) -> tuple[str, str]:
    """
    Call Granite LLM via watsonx.ai with retry, cache, and template fallback.

    Returns:
        Tuple of (response_text, source) where source is 'granite' or 'template'.
    """
    from app.settings import get_settings
    settings = get_settings()

    if not settings.watsonx_api_key or not settings.watsonx_project_id:
        return "", "template"

    cache_key = _get_cache_key(prompt)
    if cache_key in _cache:
        return _cache[cache_key], "granite"

    for attempt in range(retries + 1):
        try:
            from ibm_watsonx_ai import Credentials
            from ibm_watsonx_ai.foundation_models import ModelInference

            creds = Credentials(url=settings.watsonx_url, api_key=settings.watsonx_api_key)
            model = ModelInference(
                model_id=settings.watsonx_model_id,
                credentials=creds,
                project_id=settings.watsonx_project_id,
            )

            # Use chat API (newer, non-deprecated) with explicit token limit
            response = model.chat(
                messages=[{"role": "user", "content": prompt}],
                params={
                    "max_new_tokens": max(max_tokens, 20),
                    "temperature": temperature,
                    "stop_sequences": ["\n\n"],
                },
            )
            # Extract text from chat response
            result = response["choices"][0]["message"]["content"].strip()
            _cache[cache_key] = result
            return result, "granite"

        except Exception as exc:
            logger.warning("Granite call attempt %d/%d failed: %s", attempt + 1, retries + 1, exc)
            if attempt < retries:
                time.sleep(1)

    return "", "template"
