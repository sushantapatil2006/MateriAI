"""
AI service — Groq integration.

Implements the map-reduce summarization pipeline:
  1. MAP:    Summarize each text chunk individually.
  2. REDUCE: Combine chunk summaries, then generate the final
             structured output (summary, explanation, quiz).
"""
import json
import re
import logging
import time

from django.conf import settings
from groq import Groq

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Groq client configuration
# ---------------------------------------------------------------------------
_client = None

def _get_client():
    """Configure the Groq client once using the API key from settings."""
    global _client
    if _client is None:
        api_key = settings.GROQ_API_KEY
        if not api_key or api_key == "your-groq-api-key-here":
            raise RuntimeError(
                "GROQ_API_KEY is not set. "
                "Please add your API key to backend/.env"
            )
        _client = Groq(api_key=api_key)
    return _client


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------
CHUNK_SUMMARY_PROMPT = """You are an expert summarizer. Summarize the following text in 3-5 concise sentences. 
Focus on the key concepts, facts, and important details.

TEXT:
{text}

Respond with ONLY the summary, no extra commentary."""

FINAL_OUTPUT_PROMPT = """You are an expert educational AI assistant. Based on the following combined summary of a document, produce a structured JSON response.

COMBINED SUMMARY:
{summary}

You MUST respond with ONLY valid JSON in exactly this format (no markdown, no code fences, no extra text):
{{
  "summary": "A concise summary of the entire document in at most 200 words.",
  "explanation": "A detailed but simple explanation of the document's content. Use clear language suitable for a student. Cover all major topics and concepts. This should be at least 300 words.",
  "quiz": [
    {{
      "question": "The question text?",
      "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
      "answer": "A) Option 1"
    }}
  ]
}}

IMPORTANT RULES:
1. The "quiz" array MUST contain exactly 15 multiple-choice questions.
2. Each question MUST have exactly 4 options labeled A) through D).
3. The "answer" field MUST be one of the options exactly as written.
4. Questions should test understanding of key concepts from the document.
5. Include a mix of easy, medium, and hard questions.
6. Do NOT wrap the JSON in markdown code fences or add any text outside the JSON.
7. Ensure the JSON is valid and parseable."""


# ---------------------------------------------------------------------------
# Retry helper for rate limits
# ---------------------------------------------------------------------------
MAX_RETRIES = 3
BASE_RETRY_DELAY = 10  # Seconds


def _call_with_retry(func, *args, **kwargs):
    """
    Call `func` with automatic retry on rate-limit.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            exc_str = str(exc).lower()
            is_rate_limit = (
                "429" in exc_str
                or "rate limit" in exc_str
                or "quota" in exc_str
            )
            if is_rate_limit and attempt < MAX_RETRIES:
                delay = BASE_RETRY_DELAY * attempt
                logger.warning(
                    "Rate limited (attempt %d/%d). Retrying in %ds…",
                    attempt, MAX_RETRIES, delay,
                )
                time.sleep(delay)
            else:
                raise


# ---------------------------------------------------------------------------
# Core AI functions
# ---------------------------------------------------------------------------
def summarize_chunk(chunk: str) -> str:
    """
    Generate a short summary for a single text chunk.
    """
    client = _get_client()
    prompt = CHUNK_SUMMARY_PROMPT.format(text=chunk)

    try:
        response = _call_with_retry(
            client.chat.completions.create,
            model="llama-3.1-8b-instant",  # Super fast model for simple summaries
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("Groq chunk summarization failed: %s", exc)
        raise RuntimeError(f"AI summarization failed: {exc}") from exc


def generate_final_output(combined_summary: str) -> dict:
    """
    Generate the final structured output (summary, explanation, quiz).
    """
    client = _get_client()
    prompt = FINAL_OUTPUT_PROMPT.format(summary=combined_summary)

    try:
        response = _call_with_retry(
            client.chat.completions.create,
            model="llama-3.3-70b-versatile",  # Much smarter model for following complex JSON schema
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=4000
        )
        raw_text = response.choices[0].message.content.strip()
        return _parse_json_response(raw_text)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse AI JSON response: %s", exc)
        raise RuntimeError(
            "The AI returned an invalid response format. Please try again."
        ) from exc
    except Exception as exc:
        logger.error("Groq final output generation failed: %s", exc)
        raise RuntimeError(f"AI processing failed: {exc}") from exc


# ---------------------------------------------------------------------------
# Map-reduce pipeline (main entry point)
# ---------------------------------------------------------------------------
def process_text(chunks: list[str]) -> dict:
    """
    Full map-reduce pipeline.
    """
    if not chunks:
        raise ValueError("No text chunks provided.")

    logger.info("Starting map phase: %d chunk(s) to summarize.", len(chunks))

    # --- MAP phase ---
    chunk_summaries = []
    for i, chunk in enumerate(chunks):
        logger.info("Summarizing chunk %d/%d …", i + 1, len(chunks))
        summary = summarize_chunk(chunk)
        chunk_summaries.append(summary)
        # Small delay to respect rate limits
        if i < len(chunks) - 1:
            time.sleep(1)

    combined_summary = "\n\n".join(chunk_summaries)
    logger.info(
        "Map phase complete. Combined summary: %d characters.",
        len(combined_summary),
    )

    # --- REDUCE phase ---
    logger.info("Starting reduce phase — generating final output.")
    result = generate_final_output(combined_summary)

    return result


# ---------------------------------------------------------------------------
# JSON parsing helpers
# ---------------------------------------------------------------------------
def _parse_json_response(raw_text: str) -> dict:
    """
    Robustly parse a JSON response from the AI.
    """
    # Try direct parse first
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    fence_pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
    match = re.search(fence_pattern, raw_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find the first { ... } block
    brace_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    # All attempts failed
    logger.error("Could not parse JSON from AI response:\n%s", raw_text[:500])
    raise json.JSONDecodeError(
        "Could not extract valid JSON from AI response", raw_text, 0
    )
