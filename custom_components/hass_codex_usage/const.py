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
    ("primary_usage_percent", "Aktuelles Limit", "%", "mdi:gauge", None),
    ("primary_reset_time", "Aktuelles Limit – Reset", None, "mdi:timer-refresh", "timestamp"),
    ("primary_window_minutes", "Aktuelles Limit – Fenster", "min", "mdi:timer-outline", None),
    ("secondary_usage_percent", "Zweites Limit", "%", "mdi:gauge", None),
    ("secondary_reset_time", "Zweites Limit – Reset", None, "mdi:calendar-refresh", "timestamp"),
    ("secondary_window_minutes", "Zweites Limit – Fenster", "min", "mdi:calendar-clock", None),
    ("plan_type", "Plan", None, "mdi:account-circle-outline", None),
    ("available_reset_credits", "Limit-Resets verfügbar", "Resets", "mdi:restart", None),
    ("credit_balance", "Zusatz-Credits", "credits", "mdi:wallet-outline", None),
    ("spend_remaining_percent", "Budget übrig", "%", "mdi:cash-check", None),
    ("api_error", "API-Fehler", "errors", "mdi:alert-circle-outline", None),
)
