"""A curated shortlist of popular RCON commands."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import RustConfigEntry, RustRconCoordinator
from .entity import RustEntity
from .rcon import RustRconError

# Zero-argument (or fixed-argument) commands that are safe to fire from a
# dropdown without extra confirmation. Anything destructive (wipes, bans,
# kicks) needs a target/reason and belongs in the console instead.
POPULAR_COMMANDS: dict[str, str] = {
    "Write config": "server.writecfg",
    "Clear weather": "weather.clear",
    "Set time to noon": "env.time 12",
    "Set time to midnight": "env.time 0",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: RustConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([RustQuickCommand(entry.runtime_data)])


class RustQuickCommand(RustEntity, SelectEntity):
    """Run one of a curated set of popular RCON commands."""

    _attr_translation_key = "quick_command"
    _attr_icon = "mdi:console-line"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = list(POPULAR_COMMANDS)

    def __init__(self, coordinator: RustRconCoordinator) -> None:
        super().__init__(coordinator, "quick_command")

    async def async_select_option(self, option: str) -> None:
        try:
            await self.coordinator.client.async_command(POPULAR_COMMANDS[option])
        except RustRconError as err:
            raise HomeAssistantError(str(err)) from err
        self._attr_current_option = option
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
