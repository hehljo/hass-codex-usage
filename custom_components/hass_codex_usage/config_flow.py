"""Config flow for Codex Pulse."""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import (
    SOURCE_REAUTH,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import aiohttp_client

from .api import token_metadata
from .const import (
    AUTH_BASE_URL,
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
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    OAUTH_CLIENT_ID,
)


class CodexPulseConfigFlow(ConfigFlow, domain=DOMAIN):
    """Link a ChatGPT account through Codex device authorization."""

    VERSION = 1

    def __init__(self) -> None:
        self._device_auth_id: str | None = None
        self._user_code: str | None = None
        self._verification_url: str | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Start or finish OpenAI's device authorization flow."""
        if self._device_auth_id is None:
            try:
                await self._async_request_device_code()
            except aiohttp.ClientError:
                return self.async_abort(reason="cannot_connect")

        if user_input is not None:
            return await self._async_finish_device_login()
        return self._async_show_authorize_form()

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        """Reconnect a revoked or expired Codex authorization."""
        return await self.async_step_user()

    async def _async_request_device_code(self) -> None:
        """Request a short-lived device code from OpenAI."""
        session = aiohttp_client.async_get_clientsession(self.hass)
        async with session.post(
            f"{AUTH_BASE_URL}/api/accounts/deviceauth/usercode",
            json={"client_id": OAUTH_CLIENT_ID},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as response:
            response.raise_for_status()
            payload = await response.json(content_type=None)
        self._device_auth_id = payload["device_auth_id"]
        self._user_code = payload.get("user_code") or payload["usercode"]
        self._verification_url = f"{AUTH_BASE_URL}/codex/device"

    async def _async_finish_device_login(self) -> ConfigFlowResult:
        """Poll once, then exchange the returned authorization code."""
        try:
            tokens = await self._async_poll_and_exchange_tokens()
        except _AuthorizationPending:
            return self._async_show_authorize_form(errors={"base": "authorization_pending"})
        except aiohttp.ClientError:
            return self._async_show_authorize_form(errors={"base": "cannot_connect"})
        except (KeyError, TypeError):
            return self._async_show_authorize_form(errors={"base": "invalid_response"})

        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        id_token = tokens.get("id_token")
        required_tokens = (access_token, refresh_token, id_token)
        if not all(isinstance(token, str) and token for token in required_tokens):
            return self._async_show_authorize_form(errors={"base": "invalid_response"})

        metadata = token_metadata(id_token, access_token)
        unique_id = metadata["account_id"] or metadata["account_email"]
        if unique_id and self.source != SOURCE_REAUTH:
            await self.async_set_unique_id(str(unique_id))
            self._abort_if_unique_id_configured()

        data = {
            CONF_ACCESS_TOKEN: access_token,
            CONF_REFRESH_TOKEN: refresh_token,
            CONF_ID_TOKEN: id_token,
            CONF_EXPIRES_AT: metadata["expires_at"],
            CONF_ACCOUNT_ID: metadata["account_id"],
            CONF_ACCOUNT_EMAIL: metadata["account_email"],
            CONF_PLAN_TYPE: metadata["plan_type"],
        }
        title = "Codex Pulse"
        if metadata["plan_type"]:
            title = f"{title} · {metadata['plan_type']}"

        if self.source == SOURCE_REAUTH:
            entry = self._get_reauth_entry()
            if unique_id:
                await self.async_set_unique_id(str(unique_id))
                self._abort_if_unique_id_mismatch()
            return self.async_update_and_abort(
                entry,
                data_updates=data,
                unique_id=str(unique_id) if unique_id else None,
            )
        return self.async_create_entry(
            title=title,
            data=data,
            options={CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL},
        )

    async def _async_poll_and_exchange_tokens(self) -> dict[str, Any]:
        """Complete a device authorization that the user has approved."""
        session = aiohttp_client.async_get_clientsession(self.hass)
        async with session.post(
            f"{AUTH_BASE_URL}/api/accounts/deviceauth/token",
            json={"device_auth_id": self._device_auth_id, "user_code": self._user_code},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as response:
            if response.status in (403, 404):
                raise _AuthorizationPending
            response.raise_for_status()
            code_payload = await response.json(content_type=None)

        async with session.post(
            f"{AUTH_BASE_URL}/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": code_payload["authorization_code"],
                "redirect_uri": f"{AUTH_BASE_URL}/deviceauth/callback",
                "client_id": OAUTH_CLIENT_ID,
                "code_verifier": code_payload["code_verifier"],
            },
            timeout=aiohttp.ClientTimeout(total=15),
        ) as response:
            response.raise_for_status()
            return await response.json(content_type=None)

    def _async_show_authorize_form(self, errors: dict[str, str] | None = None) -> ConfigFlowResult:
        return self.async_show_form(
            step_id="user",
        data_schema=vol.Schema(
            {vol.Required("authorization_completed", default=False): bool}
        ),
            description_placeholders={
                "verification_url": self._verification_url or "",
                "user_code": self._user_code or "",
            },
            errors=errors or {},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the integration's options flow."""
        return CodexPulseOptionsFlow()


class CodexPulseOptionsFlow(OptionsFlow):
    """Tune the polling cadence."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = self.config_entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_UPDATE_INTERVAL, default=current): vol.All(
                        int, vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL)
                    )
                }
            ),
        )


class _AuthorizationPending(Exception):
    """The browser authorization has not completed yet."""
