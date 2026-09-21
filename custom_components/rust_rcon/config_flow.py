"""Config flow for Rust RCON."""
import logging
_LOGGER = logging.getLogger(__name__)

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_PORT, DOMAIN
from .coordinator import parse_serverinfo
from .rcon import RustRconAuthError, RustRconClient, RustRconError


class RustRconConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
            )
            self._abort_if_unique_id_configured()

            client = RustRconClient(
                async_get_clientsession(self.hass),
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                user_input[CONF_PASSWORD],
            )
            try:
                raw = await client.async_command("serverinfo")
                        except RustRconAuthError as err:
                _LOGGER.warning("Rust RCON auth error: %s", err)
                errors["base"] = "invalid_auth"
            except RustRconError as err:
                _LOGGER.warning("Rust RCON connect error: %s", err)
                errors["base"] = "cannot_connect"
            else:
                try:
                    title = parse_serverinfo(raw).get("Hostname") or user_input[CONF_HOST]
                except ValueError:
                    title = user_input[CONF_HOST]
                return self.async_create_entry(title=title, data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )
