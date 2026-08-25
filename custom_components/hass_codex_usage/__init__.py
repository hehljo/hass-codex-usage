"""Codex Pulse Home Assistant integration."""

from __future__ import annotations

import logging
import time
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import aiohttp_client
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CodexAuthenticationError, parse_usage, token_metadata
from .const import (
    AUTH_BASE_URL,
    CODEX_USAGE_URL,
    CONF_ACCESS_TOKEN,
    CONF_ACCOUNT_EMAIL,
    CONF_ACCOUNT_ID,
    CONF_EXPIRES_AT,
    CONF_ID_TOKEN,
    CONF_PLAN_TYPE,
    CONF_REFRESH_TOKEN,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    OAUTH_CLIENT_ID,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)

type CodexUsageConfigEntry = ConfigEntry["CodexUsageCoordinator"]


async def async_setup_entry(hass, entry: CodexUsageConfigEntry) -> bool:
    """Set up Codex Pulse from one config entry."""
    coordinator = CodexUsageCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def async_unload_entry(hass, entry: CodexUsageConfigEntry) -> bool:
    """Unload a Codex Pulse config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_options_updated(hass, entry: CodexUsageConfigEntry) -> None:
    """Apply an option change without reloading the integration."""
    entry.runtime_data.update_interval = timedelta(
        seconds=entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
    )
    await entry.runtime_data.async_request_refresh()


class CodexUsageCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch all Codex usage windows with one coordinated poll."""

    config_entry: CodexUsageConfigEntry

    def __init__(self, hass, entry: CodexUsageConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
            ),
            config_entry=entry,
            always_update=False,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Refresh the account token as needed and retrieve usage."""
        await self._async_ensure_access_token()
        headers = {
            "Authorization": f"Bearer {self.config_entry.data[CONF_ACCESS_TOKEN]}",
            "User-Agent": "codex-pulse-home-assistant",
        }
        account_id = self.config_entry.data.get(CONF_ACCOUNT_ID)
        if account_id:
            headers["ChatGPT-Account-Id"] = account_id

        try:
            session = aiohttp_client.async_get_clientsession(self.hass)
            async with session.get(
                CODEX_USAGE_URL,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as response:
                if response.status in (401, 403):
                    raise ConfigEntryAuthFailed("Codex authentication has expired")
                response.raise_for_status()
                payload = await response.json(content_type=None)
        except aiohttp.ClientResponseError as err:
            raise UpdateFailed(f"Unable to fetch Codex usage: HTTP {err.status}") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Unable to fetch Codex usage: {err}") from err

        if not isinstance(payload, dict):
            raise UpdateFailed("Codex usage returned invalid data")
        return parse_usage(payload)

    async def _async_ensure_access_token(self) -> None:
        """Refresh the OAuth token five minutes before it expires."""
        expires_at = self.config_entry.data.get(CONF_EXPIRES_AT, 0)
        if isinstance(expires_at, (int, float)) and time.time() < expires_at - 300:
            return

        refresh_token = self.config_entry.data.get(CONF_REFRESH_TOKEN)
        if not refresh_token:
            raise ConfigEntryAuthFailed("No Codex refresh token is available")

        try:
            session = aiohttp_client.async_get_clientsession(self.hass)
            async with session.post(
                f"{AUTH_BASE_URL}/oauth/token",
                data={
                    "client_id": OAUTH_CLIENT_ID,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                timeout=aiohttp.ClientTimeout(total=15),
            ) as response:
                if response.status in (400, 401, 403):
                    raise CodexAuthenticationError
                response.raise_for_status()
                tokens = await response.json(content_type=None)
        except CodexAuthenticationError as err:
            raise ConfigEntryAuthFailed("Reconnect Codex to continue") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Unable to refresh Codex token: {err}") from err

        access_token = tokens.get("access_token") if isinstance(tokens, dict) else None
        if not isinstance(access_token, str) or not access_token:
            raise ConfigEntryAuthFailed("Codex token response is incomplete")

        id_token = tokens.get("id_token")
        if not isinstance(id_token, str):
            id_token = self.config_entry.data.get(CONF_ID_TOKEN, "")
        new_refresh_token = tokens.get("refresh_token")
        if not isinstance(new_refresh_token, str) or not new_refresh_token:
            new_refresh_token = refresh_token
        metadata = token_metadata(id_token, access_token)
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data={
                **self.config_entry.data,
                CONF_ACCESS_TOKEN: access_token,
                CONF_REFRESH_TOKEN: new_refresh_token,
                CONF_ID_TOKEN: id_token,
                CONF_EXPIRES_AT: metadata["expires_at"] or time.time() + 300,
                CONF_ACCOUNT_ID: (
                    metadata["account_id"] or self.config_entry.data.get(CONF_ACCOUNT_ID)
                ),
                CONF_ACCOUNT_EMAIL: metadata["account_email"]
                or self.config_entry.data.get(CONF_ACCOUNT_EMAIL),
                CONF_PLAN_TYPE: metadata["plan_type"] or self.config_entry.data.get(CONF_PLAN_TYPE),
            },
        )
