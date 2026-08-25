# Codex Pulse für Home Assistant

[![HACS validation](https://github.com/hehljo/hass-codex-usage/actions/workflows/validate.yaml/badge.svg)](https://github.com/hehljo/hass-codex-usage/actions/workflows/validate.yaml)
[![Hassfest](https://github.com/hehljo/hass-codex-usage/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/hehljo/hass-codex-usage/actions/workflows/hassfest.yaml)
[![Tests](https://github.com/hehljo/hass-codex-usage/actions/workflows/tests.yaml/badge.svg)](https://github.com/hehljo/hass-codex-usage/actions/workflows/tests.yaml)
[![GitHub Release](https://img.shields.io/github/v/release/hehljo/hass-codex-usage?display_name=tag)](https://github.com/hehljo/hass-codex-usage/releases)
[![License](https://img.shields.io/github/license/hehljo/hass-codex-usage)](LICENSE)

![Codex Pulse Icon](custom_components/hass_codex_usage/brand/icon.png)

Codex Pulse macht die Codex-Auslastung als Home-Assistant-Sensoren sichtbar:
aktuelles und zweites Limit, deren Resets und Zeitfenster, Plan, verfügbare
Limit-Resets, Credits sowie automatisch entdeckte Zusatzlimits.

Die Integration verwendet die gleiche kurzlebige Geräteanmeldung wie die
Codex-CLI. Tokens werden nur in der Home-Assistant-Config-Entry gespeichert;
ins Log kommt kein Token.

## Installation

1. Das Repository in HACS als benutzerdefiniertes Repository vom Typ
   **Integration** hinzufügen.
2. **Codex Pulse** installieren und Home Assistant neu starten.
3. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** nach **Codex Pulse** suchen.
4. Die angezeigte OpenAI-Seite öffnen, den einmaligen Code eingeben und danach in Home Assistant bestätigen.

## HACS

[![Zum HACS-Repository hinzufügen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fhehljo%2Fhass-codex-usage)

1. HACS öffnen → oben rechts **⋮** → **Custom repositories**.
2. `https://github.com/hehljo/hass-codex-usage` eintragen und **Integration** wählen.
3. **Codex Pulse** installieren und Home Assistant neu starten.

## Sensoren

- Aktuelles Limit und zweites Limit – Prozent, Reset und Dauer.
- Plan, verfügbare Limit-Resets, Zusatz-Credits und verbleibendes Budget,
  soweit der Account diese Daten liefert.
- Dynamische Sensoren für weitere Codex- oder modellbezogene Limits.
  Verschwindet ein Limit temporär, bleibt dessen Verlauf in Home Assistant
  erhalten und der Sensor wird `unavailable`.

Das Standardintervall beträgt fünf Minuten und kann zwischen 60 und 3.600
Sekunden eingestellt werden. Das beigefügte Beispiel unter
`dashboards/codex_pulse.yaml` verwendet die beiden stabilen Limits.

## Hinweis

Das ist eine unabhängige Home-Assistant-Integration und kein OpenAI-Produkt.
Die Codex-Usage-Schnittstelle kann sich ändern; die Implementierung folgt dem
aktuellen öffentlichen Codex-Client.
