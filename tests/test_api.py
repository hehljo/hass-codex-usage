"""Unit tests for the response normalization layer."""

from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path
import unittest

_API_PATH = Path(__file__).parents[1] / "custom_components" / "hass_codex_usage" / "api.py"
_SPEC = importlib.util.spec_from_file_location("codex_pulse_api", _API_PATH)
assert _SPEC and _SPEC.loader
_API = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_API)
decode_jwt_claims = _API.decode_jwt_claims
parse_usage = _API.parse_usage
token_metadata = _API.token_metadata


class ApiTests(unittest.TestCase):
    def test_usage_parses_default_and_extra_limits(self) -> None:
        result = parse_usage(
            {
                "plan_type": "pro",
                "rate_limit": {
                    "primary_window": {
                        "used_percent": 42,
                        "limit_window_seconds": 18_000,
                        "reset_at": 1_735_689_600,
                    },
                    "secondary_window": {
                        "used_percent": 5,
                        "limit_window_seconds": 604_800,
                        "reset_at": 1_736_294_400,
                    },
                },
                "additional_rate_limits": [
                    {
                        "limit_name": "GPT-5.6 Max",
                        "metered_feature": "codex_gpt_5_6",
                        "rate_limit": {
                            "primary_window": {
                                "used_percent": 88,
                                "limit_window_seconds": 3_600,
                                "reset_at": 1_735_686_000,
                            }
                        },
                    }
                ],
                "rate_limit_reset_credits": {"available_count": 3},
                "credits": {"balance": "12.5"},
                "spend_control": {"individual_limit": {"remaining_percent": 68}},
            }
        )

        self.assertEqual(result["primary_usage_percent"], 42)
        self.assertEqual(result["primary_window_minutes"], 300)
        self.assertEqual(result["secondary_window_minutes"], 10_080)
        self.assertEqual(result["available_reset_credits"], 3)
        self.assertEqual(result["credit_balance"], "12.5")
        self.assertEqual(result["spend_remaining_percent"], 68)
        self.assertEqual(result["limits"]["codex_primary"]["remaining_percent"], 58)
        self.assertEqual(result["limits"]["codex_gpt_5_6_primary"]["used_percent"], 88)

    def test_token_metadata_reads_account_claims_without_validating_jwt(self) -> None:
        payload = {
            "email": "test@example.com",
            "exp": 1_800_000_000,
            "https://api.openai.com/auth": {
                "chatgpt_account_id": "workspace-42",
                "chatgpt_plan_type": "pro",
            },
        }
        payload_part = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        token = f"header.{payload_part}.signature"

        self.assertEqual(decode_jwt_claims(token)["email"], "test@example.com")
        self.assertEqual(token_metadata(token, token)["account_id"], "workspace-42")
        self.assertEqual(token_metadata(token, token)["plan_type"], "pro")
        self.assertEqual(token_metadata(token, token)["expires_at"], 1_800_000_000.0)


if __name__ == "__main__":
    unittest.main()
