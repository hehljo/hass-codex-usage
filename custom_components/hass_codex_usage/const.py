"""Constants for Codex Pulse."""

from homeassistant.const import Platform

DOMAIN = "hass_codex_usage"
PLATFORMS = [Platform.SENSOR]

DEFAULT_UPDATE_INTERVAL = 300
MIN_UPDATE_INTERVAL = 60
MAX_UPDATE_INTERVAL = 3600

AUTH_BASE_URL = "https://auth.openai.com"
CODEX_USAGE_URL = "https://chatgpt.com/backend-api/wham/usage"
OAUTH_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"

CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_ID_TOKEN = "id_token"
CONF_EXPIRES_AT = "expires_at"
CONF_ACCOUNT_ID = "account_id"
CONF_ACCOUNT_EMAIL = "account_email"
CONF_PLAN_TYPE = "plan_type"
CONF_UPDATE_INTERVAL = "update_interval"

SENSOR_DEFINITIONS = (
    ("primary_usage_percent", "Primary limit usage", "%", "mdi:gauge", None),
    ("primary_reset_time", "Primary limit reset", None, "mdi:timer-refresh", "timestamp"),
    ("primary_window_minutes", "Primary limit window", "min", "mdi:timer-outline", None),
    ("secondary_usage_percent", "Secondary limit usage", "%", "mdi:gauge", None),
    ("secondary_reset_time", "Secondary limit reset", None, "mdi:calendar-refresh", "timestamp"),
    ("secondary_window_minutes", "Secondary limit window", "min", "mdi:calendar-clock", None),
    ("plan_type", "Plan", None, "mdi:account-circle-outline", None),
    ("available_reset_credits", "Available limit resets", "resets", "mdi:restart", None),
    ("credit_balance", "Additional credits", "credits", "mdi:wallet-outline", None),
    ("spend_remaining_percent", "Remaining budget", "%", "mdi:cash-check", None),
    ("api_error", "API errors", "errors", "mdi:alert-circle-outline", None),
)
