"""Config flow for Rust RCON."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_PORT, DOMAIN
from .rcon import RustRconAuthError, RustRconClient, RustRconError

_LOGGER = logging.getLogger(__name__)


def _schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Required(CONF_PASSWORD): str,
        }
    )


class RustRconConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def _async_test_connection(
        self, user_input: dict[str, Any]
    ) -> dict[str, str]:
        """Try to connect, returning any errors."""
        client = RustRconClient(
            async_get_clientsession(self.hass),
            user_input[CONF_HOST],
            user_input[CONF_PORT],
            user_input[CONF_PASSWORD],
        )
        try:
            await client.async_command("serverinfo")
        except RustRconAuthError as err:
            _LOGGER.warning("Rust RCON auth error: %s", err)
            return {"base": "invalid_auth"}
        except RustRconError as err:
            _LOGGER.warning("Rust RCON connect error: %s", err)
            return {"base": "cannot_connect"}
        return {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
            )
            self._abort_if_unique_id_configured()

            errors = await self._async_test_connection(user_input)
            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_HOST], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(_schema(), user_input),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Allow the host/port/password to be updated without deleting the entry."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            if (
                f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                != entry.unique_id
            ):
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                )
                self._abort_if_unique_id_configured()

            errors = await self._async_test_connection(user_input)
            if not errors:
                return self.async_update_reload_and_abort(
                    entry, title=user_input[CONF_HOST], data=user_input
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                _schema(), user_input or entry.data
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle a password (or other) change once the server stops authenticating."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()

        if user_input is not None:
            merged = {**entry.data, **user_input}
            errors = await self._async_test_connection(merged)
            if not errors:
                return self.async_update_reload_and_abort(
                    entry, title=merged[CONF_HOST], data=merged
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema({vol.Required(CONF_PASSWORD): str}), user_input
            ),
            errors=errors,
        )
