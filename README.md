# Codex Pulse for Home Assistant

[![HACS validation](https://github.com/hehljo/hass-codex-usage/actions/workflows/validate.yaml/badge.svg)](https://github.com/hehljo/hass-codex-usage/actions/workflows/validate.yaml)
[![Hassfest](https://github.com/hehljo/hass-codex-usage/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/hehljo/hass-codex-usage/actions/workflows/hassfest.yaml)
[![Tests](https://github.com/hehljo/hass-codex-usage/actions/workflows/tests.yaml/badge.svg)](https://github.com/hehljo/hass-codex-usage/actions/workflows/tests.yaml)
[![GitHub Release](https://img.shields.io/github/v/release/hehljo/hass-codex-usage?display_name=tag)](https://github.com/hehljo/hass-codex-usage/releases)
[![License](https://img.shields.io/github/license/hehljo/hass-codex-usage)](LICENSE)

![Codex Pulse Icon](custom_components/hass_codex_usage/brand/icon.png)

Codex Pulse brings Codex usage into Home Assistant: primary and secondary
limits, reset times, window durations, plan, available resets, credits, and
automatically discovered additional limits.

The integration uses the same short-lived device authorization as Codex CLI.
Tokens are stored only in the Home Assistant config entry and are never logged.

## Install with HACS

1. Open HACS → **⋮** → **Custom repositories**.
2. Add `https://github.com/hehljo/hass-codex-usage` and select **Integration**.
3. Install **Codex Pulse** and restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration**, then choose
   **Codex Pulse**.
5. Open the shown OpenAI page, enter the one-time code, and confirm in Home
   Assistant.

[![Add repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fhehljo%2Fhass-codex-usage)

## Sensors

- Current and secondary limits: percentage, reset time, and window duration.
- Plan, available limit resets, additional credits, and remaining budget when
  supplied by the account.
- Dynamic sensors for Codex or model-specific limits. If a limit temporarily
  disappears, its Home Assistant history stays intact and the sensor becomes
  `unavailable`.

The default polling interval is five minutes and can be set from 60 to 3,600
seconds. The sample dashboard in `dashboards/codex_pulse.yaml` uses the two
stable limits.

## Notes

This is an independent Home Assistant integration, not an OpenAI product. The
Codex usage interface may change; the implementation follows the current public
Codex client behavior.
