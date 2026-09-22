"""A curated shortlist of popular RCON commands."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import OPT_CUSTOM_COMMANDS
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


def _player_label(player: dict) -> str:
    name = player.get("DisplayName") or "Unknown"
    steam_id = player.get("SteamID") or "?"
    return f"{name} ({steam_id})"


async def async_setup_entry(
    hass: HomeAssistant, entry: RustConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities([RustQuickCommand(coordinator), RustTargetPlayer(coordinator)])


class RustQuickCommand(RustEntity, SelectEntity):
    """Run one of the built-in popular commands, or a user-added one.

    Custom commands are managed from the integration's "Configure" option
    (Settings -> Devices & services -> Rust RCON -> Configure) and stored in
    the config entry's options; a custom command with the same label as a
    built-in one overrides it.
    """

    _attr_translation_key = "quick_command"
    _attr_icon = "mdi:console-line"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: RustRconCoordinator) -> None:
        super().__init__(coordinator, "quick_command")

    @property
    def _commands(self) -> dict[str, str]:
        custom = self.coordinator.config_entry.options.get(OPT_CUSTOM_COMMANDS, {})
        return {**POPULAR_COMMANDS, **custom}

    @property
    def options(self) -> list[str]:
        return list(self._commands)

    async def async_select_option(self, option: str) -> None:
        try:
            await self.coordinator.client.async_command(self._commands[option])
        except RustRconError as err:
            raise HomeAssistantError(str(err)) from err
        self._attr_current_option = option
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()


class RustTargetPlayer(RustEntity, SelectEntity):
    """Pick an online player for the kick/ban buttons to act on."""

    _attr_translation_key = "target_player"
    _attr_icon = "mdi:account-search"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: RustRconCoordinator) -> None:
        super().__init__(coordinator, "target_player")

    @property
    def options(self) -> list[str]:
        return [_player_label(p) for p in (self.coordinator.data or {}).get("PlayerList", [])]

    @property
    def current_option(self) -> str | None:
        selected = self.coordinator.selected_player
        if selected is None:
            return None
        label = _player_label(selected)
        return label if label in self.options else None

    async def async_select_option(self, option: str) -> None:
        for player in (self.coordinator.data or {}).get("PlayerList", []):
            if _player_label(player) == option:
                self.coordinator.selected_player = player
                break
        self.async_write_ha_state()
