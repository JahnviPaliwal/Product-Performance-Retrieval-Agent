"""Structured logging module for recording LLM call telemetry without logging raw user data.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class StructuredJsonFormatter(logging.Formatter):
    """Custom formatter outputting logs as structured JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "telemetry"):
            log_obj["telemetry"] = getattr(record, "telemetry")
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def get_logger(name: str = "analytics_agent") -> logging.Logger:
    """Retrieve or configure a structured logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


_telemetry_logger = get_logger("analytics_agent.telemetry")


def log_llm_call(
    model: str,
    prompt_chars: int,
    latency_ms: float,
    usage: Optional[Any] = None,
    status: str = "success",
    error_message: Optional[str] = None,
) -> None:
    """Record privacy-preserving metrics for an LLM interaction.

    Never logs raw user data, dataset rows, or API keys.

    Args:
        model: Model identifier (e.g. 'llama-3.1-8b-instant').
        prompt_chars: Character length of the compiled prompt.
        latency_ms: Round-trip execution time in milliseconds.
        usage: Optional Groq usage object containing token metrics.
        status: Call status ('success', 'retry', 'fallback', 'error').
        error_message: Sanitized error description if call failed.
    """
    telemetry: Dict[str, Any] = {
        "event": "llm_completion",
        "model": model,
        "prompt_chars": prompt_chars,
        "latency_ms": round(latency_ms, 2),
        "status": status,
    }

    if usage is not None:
        telemetry["prompt_tokens"] = getattr(usage, "prompt_tokens", None)
        telemetry["completion_tokens"] = getattr(usage, "completion_tokens", None)
        telemetry["total_tokens"] = getattr(usage, "total_tokens", None)

    if error_message:
        telemetry["error"] = error_message

    record = logging.LogRecord(
        name="analytics_agent.telemetry",
        level=logging.INFO if status in {"success", "fallback"} else logging.WARNING,
        pathname=__file__,
        lineno=0,
        msg=f"LLM call {status} in {latency_ms:.1f}ms",
        args=(),
        exc_info=None,
    )
    setattr(record, "telemetry", telemetry)
    _telemetry_logger.handle(record)
