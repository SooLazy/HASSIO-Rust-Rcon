"""Data coordinator for Rust RCON."""
from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL
from .rcon import RustRconClient, RustRconError

_LOGGER = logging.getLogger(__name__)

type RustConfigEntry = ConfigEntry[RustRconCoordinator]


def parse_serverinfo(raw: str) -> dict[str, Any]:
    """Extract the JSON object from a `serverinfo` reply."""
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON in serverinfo reply")
    return json.loads(raw[start : end + 1])


class RustRconCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls `serverinfo` on an interval."""

    config_entry: RustConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: RustConfigEntry, client: RustRconClient
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return parse_serverinfo(await self.client.async_command("serverinfo"))
        except (RustRconError, ValueError) as err:
            raise UpdateFailed(f"Error fetching Rust server info: {err}") from err
