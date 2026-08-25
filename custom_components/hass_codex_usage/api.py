"""Small, dependency-free client helpers for Codex Pulse."""

from __future__ import annotations

import base64
import binascii
import json
from datetime import UTC, datetime
from typing import Any


class CodexUsageError(Exception):
    """Base error for a Codex usage request."""


class CodexAuthenticationError(CodexUsageError):
    """The stored Codex authorization is no longer valid."""


def decode_jwt_claims(token: str | None) -> dict[str, Any]:
    """Return unverified claims used only to identify a token's account."""
    if not isinstance(token, str):
        return {}
    try:
        _header, payload, _signature = token.split(".", 2)
        padded_payload = payload + "=" * (-len(payload) % 4)
        decoded = base64.urlsafe_b64decode(padded_payload)
        claims = json.loads(decoded)
    except (ValueError, UnicodeDecodeError, binascii.Error, json.JSONDecodeError):
        return {}
    return claims if isinstance(claims, dict) else {}


def token_metadata(id_token: str | None, access_token: str | None) -> dict[str, Any]:
    """Extract non-secret account metadata from OAuth tokens."""
    claims = decode_jwt_claims(id_token) or decode_jwt_claims(access_token)
    auth = claims.get("https://api.openai.com/auth", {})
    profile = claims.get("https://api.openai.com/profile", {})
    if not isinstance(auth, dict):
        auth = {}
    if not isinstance(profile, dict):
        profile = {}

    return {
        "account_id": auth.get("chatgpt_account_id"),
        "account_email": claims.get("email") or profile.get("email"),
        "plan_type": auth.get("chatgpt_plan_type"),
        "expires_at": _numeric_claim(decode_jwt_claims(access_token), "exp"),
    }


def parse_usage(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize the Codex usage response into entity-ready values."""
    result: dict[str, Any] = {"limits": {}}
    result["plan_type"] = payload.get("plan_type")

    reset_credits = payload.get("rate_limit_reset_credits")
    if isinstance(reset_credits, dict):
        result["available_reset_credits"] = reset_credits.get("available_count")

    _add_limit_windows(
        result,
        key="codex",
        label="Codex",
        limit=payload.get("rate_limit"),
        is_default=True,
    )

    for index, extra in enumerate(payload.get("additional_rate_limits") or []):
        if not isinstance(extra, dict):
            continue
        key = str(extra.get("metered_feature") or extra.get("limit_name") or f"limit_{index + 1}")
        label = str(extra.get("limit_name") or key.replace("_", " ").title())
        _add_limit_windows(result, key=key, label=label, limit=extra.get("rate_limit"))

    credits = payload.get("credits")
    if isinstance(credits, dict):
        result["credit_balance"] = credits.get("balance")

    spend_control = payload.get("spend_control")
    if isinstance(spend_control, dict):
        individual_limit = spend_control.get("individual_limit")
        if isinstance(individual_limit, dict):
            result["spend_remaining_percent"] = individual_limit.get("remaining_percent")

    return {key: value for key, value in result.items() if value is not None}


def _add_limit_windows(
    result: dict[str, Any],
    *,
    key: str,
    label: str,
    limit: Any,
    is_default: bool = False,
) -> None:
    if not isinstance(limit, dict):
        return
    windows = ("primary", "secondary")
    for window_name in windows:
        window = limit.get(f"{window_name}_window")
        if not isinstance(window, dict):
            continue
        normalized = _window_data(window)
        if not normalized:
            continue
        if is_default:
            result[f"{window_name}_usage_percent"] = normalized.get("used_percent")
            result[f"{window_name}_window_minutes"] = normalized.get("window_minutes")
            result[f"{window_name}_reset_time"] = normalized.get("resets_at")
            continue
        limit_key = f"{key}_{window_name}"
        result["limits"][limit_key] = {
            "label": f"{label} {window_name.title()} limit",
            "limit_id": key,
            "window": window_name,
            **normalized,
        }


def _window_data(window: dict[str, Any]) -> dict[str, Any]:
    used_percent = window.get("used_percent")
    if used_percent is None:
        return {}
    window_seconds = window.get("limit_window_seconds")
    window_minutes = None
    if isinstance(window_seconds, (int, float)) and window_seconds > 0:
        window_minutes = int((window_seconds + 59) // 60)
    return {
        "used_percent": used_percent,
        "remaining_percent": (
            max(0, 100 - used_percent) if isinstance(used_percent, (int, float)) else None
        ),
        "window_minutes": window_minutes,
        "resets_at": _iso_timestamp(window.get("reset_at")),
    }


def _iso_timestamp(value: Any) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    return datetime.fromtimestamp(value, tz=UTC).isoformat()


def _numeric_claim(claims: dict[str, Any], key: str) -> float | None:
    value = claims.get(key)
    return float(value) if isinstance(value, (int, float)) else None
