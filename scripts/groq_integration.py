#!/usr/bin/env python3
"""Groq analysis integration helpers for the E2B demo agent.

This module follows the implementation guidelines outlined in
`HACKATHON_PARALLEL_WORKSTREAMS.md` (Workstream 3: Groq Integration).
It provides a thin wrapper around the Groq chat completions API with
basic rate-limit handling, prompt presets for hackathon demos, and a
CLI so engineers can exercise the helper quickly during development.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

try:
    from groq import Groq  # type: ignore
except ModuleNotFoundError as exc:  # pragma: no cover - guard for missing optional dep
    raise ModuleNotFoundError(
        "The 'groq' package is required. Install it with `pip install groq`."
    ) from exc


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Primary / fallback models requested in the hackathon spec.
DEFAULT_MODEL = "mixtral-8x7b-32768"
FALLBACK_MODEL = "llama-3.1-8b-instant"

# Default system instruction used for textual document analysis.
DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant analyzing TweekIT conversions."

# Simple set of demo prompts called out in the workstream plus a couple of extras
# so we always have 5+ scenarios ready for live demos.
DEMO_PROMPTS: Dict[str, str] = {
    "resume_analysis": (
        "Analyze this resume and extract the candidate's key skills, years of "
        "experience, and unique qualifications. Provide a fit score (1-10) for "
        "a Software Engineer position."
    ),
    "document_summary": (
        "Summarize the most important takeaways from this document in three "
        "concise bullet points."
    ),
    "data_insights": (
        "Extract noteworthy metrics, trends, and outliers from the provided "
        "content. Present the findings as bullet points with short explanations."
    ),
    "support_ticket_triage": (
        "Classify the severity of this support ticket, list suspected root "
        "causes, and recommend the next actions for the on-call engineer."
    ),
    "compliance_review": (
        "Identify any potential compliance or policy risks described in the "
        "content and outline the remediation steps the team should take."
    ),
}


class GroqIntegrationError(RuntimeError):
    """Raised when the Groq integration fails to complete successfully."""


@dataclass(frozen=True)
class GroqAnalysisResult:
    """Structured Groq response returned by :func:`analyze_with_groq`."""

    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int


def _resolve_api_key(explicit_api_key: Optional[str]) -> str:
    """Return the Groq API key or raise a helpful error."""
    api_key = (explicit_api_key or os.getenv("GROQ_API_KEY") or "").strip()
    if not api_key:
        raise GroqIntegrationError(
            "Missing Groq API key. Set the GROQ_API_KEY environment variable or "
            "pass api_key explicitly."
        )
    return api_key


def _iter_models(primary: str, fallback: Optional[str]) -> Iterable[str]:
    """Yield the models to try in order."""
    tried: List[str] = []
    for candidate in (primary, fallback):
        if candidate and candidate not in tried:
            tried.append(candidate)
            yield candidate


def _should_retry(exception: Exception) -> Tuple[bool, float]:
    """Return (should_retry, sleep_seconds) for the provided exception."""
    # Default backoff when we detect throttling conditions.
    backoff_seconds = 2.0

    status = getattr(exception, "status_code", None) or getattr(
        getattr(exception, "response", None), "status_code", None
    )
    message = str(exception).lower()

    if status in {408, 429, 500, 502, 503}:
        return True, backoff_seconds

    throttled = any(keyword in message for keyword in ("rate limit", "retry later", "too many requests"))
    if throttled:
        return True, backoff_seconds

    return False, 0.0


def analyze_with_groq(
    content: str,
    prompt: str,
    model: str = DEFAULT_MODEL,
    *,
    api_key: Optional[str] = None,
    fallback_model: Optional[str] = FALLBACK_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    retries: int = 2,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> GroqAnalysisResult:
    """Analyze content using Groq chat completions.

    Args:
        content: The document text or description to analyze.
        prompt: A natural language instruction appended to the content.
        model: Primary Groq model identifier.
        api_key: Optional explicit API key (otherwise GROQ_API_KEY is used).
        fallback_model: Alternative model to try if the primary fails.
        temperature: Sampling temperature used by the model.
        max_tokens: Maximum tokens to allocate for the completion.
        retries: Number of retries for transient errors per model.
        system_prompt: System role instruction for the LLM.

    Returns:
        GroqAnalysisResult containing the response content and metadata.

    Raises:
        GroqIntegrationError: If no response can be obtained after retries.
    """
    if not content:
        raise GroqIntegrationError("Content payload must not be empty.")
    if not prompt:
        raise GroqIntegrationError("Prompt must not be empty.")

    client = Groq(api_key=_resolve_api_key(api_key))
    errors: List[str] = []

    for active_model in _iter_models(model, fallback_model):
        attempt = 0
        while attempt <= retries:
            try:
                logger.debug("Calling Groq model %s (attempt %s)", active_model, attempt + 1)
                response = client.chat.completions.create(
                    model=active_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"{prompt}\n\nContent:\n{content}"},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                choice = response.choices[0]
                content_text = (choice.message.content or "").strip()
                if not content_text:
                    raise GroqIntegrationError("Groq returned an empty response.")

                usage = getattr(response, "usage", None) or {}
                prompt_tokens = int(getattr(usage, "prompt_tokens", usage.get("prompt_tokens", 0)))
                completion_tokens = int(getattr(usage, "completion_tokens", usage.get("completion_tokens", 0)))

                return GroqAnalysisResult(
                    content=content_text,
                    model=response.model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                )

            except Exception as exc:  # noqa: BLE001 - groq SDK raises broad exceptions
                attempt += 1
                should_retry, sleep_seconds = _should_retry(exc)
                logger.warning("Groq call failed with %s: %s", exc.__class__.__name__, exc)

                if should_retry and attempt <= retries:
                    logger.info("Retrying Groq request after %.1f seconds (attempt %s/%s).", sleep_seconds, attempt, retries + 1)
                    if sleep_seconds > 0:
                        time.sleep(sleep_seconds)
                    continue

                # No retry left for this model
                errors.append(f"{active_model}: {exc}")
                break

    detail = "; ".join(errors) if errors else "unknown error"
    raise GroqIntegrationError(f"Unable to obtain Groq analysis after retries ({detail}).")


def list_demo_prompts() -> List[str]:
    """Return demo prompt keys available for quick-start scenarios."""
    return list(DEMO_PROMPTS.keys())


def _build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a quick Groq analysis for hackathon demos.")
    parser.add_argument(
        "--prompt-key",
        choices=sorted(DEMO_PROMPTS.keys()),
        default="document_summary",
        help="Demo prompt preset to use (default: document_summary).",
    )
    parser.add_argument(
        "--content",
        required=False,
        help="Content to analyze. If omitted, content is read from STDIN.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Primary Groq model to use (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--fallback",
        default=FALLBACK_MODEL,
        help=f"Fallback Groq model (default: {FALLBACK_MODEL}). Use '' to disable.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="Maximum tokens allocated for the completion (default: 1024).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature (default: 0.7).",
    )
    return parser


def _cli_entry(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_cli_parser()
    args = parser.parse_args(argv)

    content = args.content or sys.stdin.read()
    if not content.strip():
        parser.error("No content provided. Pass --content or pipe text via STDIN.")

    prompt = DEMO_PROMPTS[args.prompt_key]
    fallback = args.fallback or None

    try:
        result = analyze_with_groq(
            content=content,
            prompt=prompt,
            model=args.model,
            fallback_model=fallback,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
        )
    except GroqIntegrationError as exc:
        logger.error("Groq analysis failed: %s", exc)
        return 1

    print(f"Model: {result.model}")
    print(f"Prompt tokens: {result.prompt_tokens}, Completion tokens: {result.completion_tokens}")
    print("\n=== Groq Analysis ===\n")
    print(result.content)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual testing entry point
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    sys.exit(_cli_entry())
