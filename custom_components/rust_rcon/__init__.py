"""Rust RCON integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .const import (
    ATTR_COMMAND,
    ATTR_ENTRY_ID,
    ATTR_MESSAGE,
    DOMAIN,
    SERVICE_SAY,
    SERVICE_SEND_COMMAND,
)
from .coordinator import RustConfigEntry, RustRconCoordinator
from .rcon import RustRconClient, RustRconError

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SEND_SCHEMA = vol.Schema(
    {vol.Required(ATTR_COMMAND): cv.string, vol.Optional(ATTR_ENTRY_ID): cv.string}
)
SAY_SCHEMA = vol.Schema(
    {vol.Required(ATTR_MESSAGE): cv.string, vol.Optional(ATTR_ENTRY_ID): cv.string}
)


def _resolve(hass: HomeAssistant, entry_id: str | None) -> RustRconCoordinator:
    loaded = [
        e
        for e in hass.config_entries.async_entries(DOMAIN)
        if e.state is ConfigEntryState.LOADED
    ]
    if entry_id:
        for e in loaded:
            if e.entry_id == entry_id:
                return e.runtime_data
        raise ServiceValidationError(f"No loaded Rust RCON entry with id {entry_id}")
    if not loaded:
        raise ServiceValidationError("No Rust RCON server is loaded")
    if len(loaded) > 1:
        raise ServiceValidationError("Multiple servers configured: pass entry_id")
    return loaded[0].runtime_data


async def _run(hass: HomeAssistant, entry_id: str | None, command: str) -> dict:
    coordinator = _resolve(hass, entry_id)
    try:
        response = await coordinator.client.async_command(command)
    except RustRconError as err:
        raise HomeAssistantError(str(err)) from err
    await coordinator.async_request_refresh()
    return {"response": response}


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register services once."""

    async def send_command(call: ServiceCall) -> dict:
        return await _run(hass, call.data.get(ATTR_ENTRY_ID), call.data[ATTR_COMMAND])

    async def say(call: ServiceCall) -> dict:
        msg = call.data[ATTR_MESSAGE].replace('"', "'")
        return await _run(hass, call.data.get(ATTR_ENTRY_ID), f'say "{msg}"')

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_COMMAND,
        send_command,
        schema=SEND_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SAY,
        say,
        schema=SAY_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: RustConfigEntry) -> bool:
    client = RustRconClient(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_PASSWORD],
    )
    coordinator = RustRconCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: RustConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
