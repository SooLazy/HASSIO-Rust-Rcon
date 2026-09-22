"""Data coordinator for Rust RCON."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL
from .parsers import parse_playerlist, parse_serverinfo
from .rcon import RustRconAuthError, RustRconClient, RustRconError

_LOGGER = logging.getLogger(__name__)

type RustConfigEntry = ConfigEntry[RustRconCoordinator]


class RustRconCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls `serverinfo` (and `playerlist`) on an interval."""

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
        self.selected_player: dict[str, Any] | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            info = parse_serverinfo(await self.client.async_command("serverinfo"))
        except RustRconAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except (RustRconError, ValueError) as err:
            raise UpdateFailed(f"Error fetching Rust server info: {err}") from err

        try:
            info["PlayerList"] = parse_playerlist(
                await self.client.async_command("playerlist")
            )
        except RustRconAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except RustRconError as err:
            # Not every server/plugin setup answers this command; don't fail
            # the whole update over it, just keep the previous list (if any).
            _LOGGER.debug("Could not fetch playerlist: %s", err)
            info["PlayerList"] = (self.data or {}).get("PlayerList", [])

        return info
