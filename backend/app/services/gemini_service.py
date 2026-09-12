"""Gemini Vision integration for LegalMetriX label extraction."""

import json
import logging
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from PIL import Image, UnidentifiedImageError

from app.schemas import LabelAnalysis

# Defensive: makes standalone imports of this module work even when the
# caller did not already call load_dotenv() (main.py does both).
load_dotenv()

logger = logging.getLogger(__name__)

# Model is configurable via env so it can be rolled forward without code
# changes. gemini-3.8-flash is the current recommended flash-tier model and
# is available on this API key (verified via models.list()).
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# Fallback model if the primary is temporarily overloaded. Must also be
# available on the API key. gemini-3.6-flash is stable and verified.
FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")

# Retry policy: max 2 attempts with 2 s backoff; transient 5xx are retried,
# other status codes fail immediately. Configured via env for tests/ops.
_MAX_RETRIES = int(os.getenv("GEMINI_MAX_RETRIES", "2"))
_RETRY_DELAY_S = float(os.getenv("GEMINI_RETRY_DELAY_S", "2.0"))
_TRANSIENT_CODES = {500, 502, 503, 504}

_client: genai.Client | None = None


class LabelAnalysisError(Exception):
    """Raised when Gemini cannot produce a usable label analysis."""


def _get_client() -> genai.Client:
    """Lazy, cached Gemini client. Creating it at call time (instead of at
    import time) keeps module import side-effect free and makes the service
    easy to test/mock."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise LabelAnalysisError(
                "GEMINI_API_KEY is not set. Add it to .env or the environment."
            )
        _client = genai.Client(api_key=api_key)
    return _client


def _parse_json(text: str) -> dict:
    """Parse Gemini's JSON response defensively.

    With response_mime_type=application/json the text should be clean JSON,
    but a small fallback strips common markdown code fences just in case.
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        cleaned = (
            text.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise LabelAnalysisError(
                "Gemini returned output that is not valid JSON"
            ) from exc

    if not isinstance(data, dict):
        raise LabelAnalysisError(
            "Gemini returned JSON that is not an object"
        )
    return data


def _generate(
    prompt: str,
    image,
    config: types.GenerateContentConfig,
) -> types.GenerateContentResponse:
    """Call the Gemini API with bounded retry and automatic fallback.

    On the first attempt the primary ``MODEL`` is used. If it returns a
    transient server error (500/502/503/504) or the call fails at the network
    level, the next attempt switches to ``FALLBACK_MODEL`` and waits
    ``_RETRY_DELAY_S`` seconds. All subsequent retries stay on the fallback.

    Non-retryable client errors (e.g. invalid request, 429 rate-limit) are
    raised immediately.
    """
    models = [MODEL]
    if FALLBACK_MODEL and FALLBACK_MODEL != MODEL:
        models.append(FALLBACK_MODEL)

    last_exc: errors.APIError | None = None
    for attempt in range(1 + _MAX_RETRIES):
        current_model = models[min(attempt, len(models) - 1)]

        try:
            return _get_client().models.generate_content(
                model=current_model,
                contents=[prompt, image],
                config=config,
            )
        except errors.APIError as exc:
            last_exc = exc
            code = getattr(exc, "code", None)

            # Non-retryable 4xx (except 429) fail immediately.
            if code is not None and 400 <= code < 500 and code not in (429,):
                raise

            if attempt < _MAX_RETRIES:
                wait = _RETRY_DELAY_S * (attempt + 1)
                logger.warning(
                    "Gemini error (model=%s, code=%s, attempt=%d/%d), "
                    "retrying in %.1fs …",
                    current_model,
                    code,
                    attempt + 1,
                    1 + _MAX_RETRIES,
                    wait,
                )
                time.sleep(wait)

    # Final failure — propagate the last API error so the caller can log it.
    raise last_exc  # type: ignore[misc]


def analyze_label(image_path: str) -> dict:
    """Extract legal-metrology compliance fields from a packaged-commodity
    label image using Gemini Vision.

    Args:
        image_path: Path to a readable image file on disk.

    Returns:
        dict: The extracted label fields (see app.schemas.LabelAnalysis).

    Raises:
        LabelAnalysisError: if the image is invalid or Gemini fails to
            produce a usable JSON analysis.
    """
    try:
        # load() reads pixel data into memory so the file handle can be
        # closed immediately; the in-memory image stays usable by the SDK.
        with Image.open(image_path) as image:
            image.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise LabelAnalysisError(
            f"Unable to read image as a picture: {exc}"
        ) from exc

    prompt = """Extract every visible compliance field from the package image.

Pay special attention to:
- MRP
- Net Weight
- Net Quantity
- Packed On
- Packaging Date
- Manufacturing Date
- Import Date
- Batch Number
- Best Before
- Use By Date
- FSSAI License Number

Do not infer values.
Only return values explicitly visible.
Return empty string if unreadable."""

    config = types.GenerateContentConfig(
        temperature=0.2,
        response_mime_type="application/json",
        response_json_schema=LabelAnalysis.model_json_schema(),
    )

    try:
        response = _generate(prompt, image, config)
    except errors.APIError as exc:
        raise LabelAnalysisError(
            f"Gemini API request failed: {exc}"
        ) from exc

    text = getattr(response, "text", None)
    if not text:
        raise LabelAnalysisError(
            "Gemini returned an empty response"
        )

    return _parse_json(text)