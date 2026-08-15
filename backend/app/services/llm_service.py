"""
Clinexa — LLM Service (Groq)
Phase 2: Full implementation using the Groq Python SDK.

Provides:
  - completion()          — general chat completion
  - completion_json()     — forces JSON object output (for extraction)
  - classify_document()   — returns one of 4 document type labels
  - extract_parameters()  — returns structured lab parameters
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

from app.core.config import settings

log = logging.getLogger(__name__)

# Groq pricing (per 1M tokens) as of mid-2025 for llama3-8b-8192
GROQ_INPUT_PRICE_PER_1M = 0.05
GROQ_OUTPUT_PRICE_PER_1M = 0.10

CLASSIFICATION_PROMPT = """You are a medical document classifier.
Classify the following document text into exactly ONE of these categories:
  blood_test | prescription | imaging_report | other

Respond with ONLY the category label — no explanation, no punctuation.

Document text:
{text}
"""

EXTRACTION_PROMPT = """You are a medical lab data extractor.
Extract ALL numeric lab parameters from the text below.

Return a JSON object with a single key "parameters" containing an array.
Each element must have exactly these fields:
  - parameter: string (name of the test, e.g. "Hemoglobin")
  - value: number (the measured numeric value, null if not found)
  - unit: string (e.g. "g/dL", null if not found)
  - reference_range: object with keys "min" (number|null) and "max" (number|null)
  - page: integer ({page_number})

Rules:
- Do NOT infer or guess values not explicitly stated.
- Do NOT include qualitative results (e.g. "Positive", "Negative") as numeric values.
- If a reference range is expressed as "> X", set min=X and max=null. If "< X", set min=null and max=X.
- Include every distinct parameter found.

Document text (page {page_number}):
{text}
"""


class LLMService:
    """
    Wrapper around the Groq SDK.
    All calls are synchronous (run in thread pool via asyncio.to_thread in agents).
    """

    def __init__(
        self,
        model: str = "llama3-8b-8192",
        fast_model: str = "llama3-8b-8192",
    ) -> None:
        self.model = model
        self.fast_model = fast_model
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            from groq import Groq
            self._client = Groq(api_key=settings.GROQ_API_KEY)
        return self._client

    # ── Core helpers ──────────────────────────────────────────────────────────

    def completion(
        self,
        system_prompt: str,
        user_message: str,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.1,
    ) -> tuple[str, dict]:
        """
        Run a chat completion.
        Returns (response_text, usage_dict).
        usage_dict has keys: input_tokens, output_tokens, estimated_cost_usd.
        """
        client = self._get_client()
        t0 = time.perf_counter()
        resp = client.chat.completions.create(
            model=model or self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency_ms = int((time.perf_counter() - t0) * 1000)

        content = resp.choices[0].message.content or ""
        usage = resp.usage

        in_tokens = usage.prompt_tokens if usage else 0
        out_tokens = usage.completion_tokens if usage else 0
        cost = (
            (in_tokens * GROQ_INPUT_PRICE_PER_1M / 1_000_000)
            + (out_tokens * GROQ_OUTPUT_PRICE_PER_1M / 1_000_000)
        )

        log.info(
            "llm.completion",
            model=model or self.model,
            in_tokens=in_tokens,
            out_tokens=out_tokens,
            cost_usd=round(cost, 6),
            latency_ms=latency_ms,
        )

        return content, {
            "input_tokens": in_tokens,
            "output_tokens": out_tokens,
            "estimated_cost_usd": cost,
            "latency_ms": latency_ms,
        }

    def completion_json(
        self,
        system_prompt: str,
        user_message: str,
        model: Optional[str] = None,
        max_tokens: int = 2048,
    ) -> tuple[dict, dict]:
        """
        Run a completion and parse the response as JSON.
        Returns (parsed_dict, usage_dict).
        """
        client = self._get_client()
        t0 = time.perf_counter()
        resp = client.chat.completions.create(
            model=model or self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.0,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        latency_ms = int((time.perf_counter() - t0) * 1000)

        content = resp.choices[0].message.content or "{}"
        usage = resp.usage
        in_tokens = usage.prompt_tokens if usage else 0
        out_tokens = usage.completion_tokens if usage else 0
        cost = (
            (in_tokens * GROQ_INPUT_PRICE_PER_1M / 1_000_000)
            + (out_tokens * GROQ_OUTPUT_PRICE_PER_1M / 1_000_000)
        )

        log.info(
            "llm.json_completion",
            in_tokens=in_tokens,
            out_tokens=out_tokens,
            cost_usd=round(cost, 6),
            latency_ms=latency_ms,
        )

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            log.error("llm.json_parse_error", content=content[:200], error=str(exc))
            parsed = {}

        return parsed, {
            "input_tokens": in_tokens,
            "output_tokens": out_tokens,
            "estimated_cost_usd": cost,
            "latency_ms": latency_ms,
        }

    # ── Domain-specific methods ───────────────────────────────────────────────

    def classify_document(self, text: str) -> str:
        """
        Classify a document into one of:
          blood_test | prescription | imaging_report | other

        Returns the label string.
        """
        VALID = {"blood_test", "prescription", "imaging_report", "other"}
        # Use only the first 2000 chars for classification (cheap & fast)
        snippet = text[:2000].strip()
        prompt = CLASSIFICATION_PROMPT.format(text=snippet)

        content, _ = self.completion(
            system_prompt="You are a precise medical document classifier.",
            user_message=prompt,
            model=self.fast_model,
            max_tokens=10,
            temperature=0.0,
        )
        label = content.strip().lower().strip("'\".,")
        if label not in VALID:
            log.warning("llm.classify.invalid_label: raw=%r, defaulting=other", content)
            return "other"
        return label

    def extract_parameters(self, text: str, page_number: int) -> list[dict]:
        """
        Extract lab parameters from page text.
        Returns a list of raw dicts (status NOT set here — rule engine handles that).

        Each dict has:
          parameter, value, unit, ref_min, ref_max, page
        """
        if not text.strip():
            return []

        # Truncate at 4000 chars to stay within context
        snippet = text[:4000]
        user_msg = EXTRACTION_PROMPT.format(text=snippet, page_number=page_number)

        parsed, _ = self.completion_json(
            system_prompt=(
                "You are a precise medical lab data extractor. "
                "Return only valid JSON matching the requested schema."
            ),
            user_message=user_msg,
            max_tokens=2048,
        )

        raw_params = parsed.get("parameters", [])
        if not isinstance(raw_params, list):
            log.warning("llm.extract.bad_structure", parsed_keys=list(parsed.keys()))
            return []

        results = []
        for p in raw_params:
            try:
                ref = p.get("reference_range") or {}
                results.append({
                    "parameter": str(p.get("parameter", "")).strip(),
                    "value": _safe_float(p.get("value")),
                    "unit": str(p.get("unit", "")).strip() or None,
                    "ref_min": _safe_float(ref.get("min")),
                    "ref_max": _safe_float(ref.get("max")),
                    "page": int(p.get("page", page_number)),
                })
            except Exception as exc:
                log.warning("llm.extract.param_parse_error", error=str(exc), raw=p)
                continue

        # Drop entries with no parameter name
        results = [r for r in results if r["parameter"]]

        log.info(
            "llm.extract.done",
            page=page_number,
            num_params=len(results),
        )
        return results


def _safe_float(v: Any) -> Optional[float]:
    """Convert a value to float, returning None if not possible."""
    if v is None:
        return None
    try:
        f = float(v)
        return f if not (f != f) else None  # reject NaN
    except (TypeError, ValueError):
        return None


# Module-level singleton
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
