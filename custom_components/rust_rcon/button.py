"""Buttons for Rust RCON."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import RustConfigEntry, RustRconCoordinator
from .entity import RustEntity
from .rcon import RustRconError


@dataclass(frozen=True, kw_only=True)
class RustButtonDescription(ButtonEntityDescription):
    """Button description with the RCON command to run."""

    command: str


BUTTONS: tuple[RustButtonDescription, ...] = (
    RustButtonDescription(
        key="save",
        translation_key="save",
        icon="mdi:content-save",
        entity_category=EntityCategory.CONFIG,
        command="server.save",
    ),
    RustButtonDescription(
        key="restart",
        translation_key="restart",
        device_class=ButtonDeviceClass.RESTART,
        entity_category=EntityCategory.CONFIG,
        command="restart 60",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: RustConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up buttons."""
    coordinator = entry.runtime_data
    async_add_entities(
        [RustButton(coordinator, desc) for desc in BUTTONS]
        + [RustKickPlayer(coordinator), RustBanPlayer(coordinator)]
    )


class RustButton(RustEntity, ButtonEntity):
    """A button that runs a fixed RCON command."""

    entity_description: RustButtonDescription

    def __init__(
        self, coordinator: RustRconCoordinator, description: RustButtonDescription
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        try:
            await self.coordinator.client.async_command(self.entity_description.command)
        except RustRconError as err:
            raise HomeAssistantError(str(err)) from err
        await self.coordinator.async_request_refresh()


class _RustPlayerActionButton(RustEntity, ButtonEntity):
    """Base for buttons that act on whichever player select.target_player holds."""

    _command_template: str
    _no_target_error = "No player selected. Choose one in Target player first."

    async def async_press(self) -> None:
        player = self.coordinator.selected_player
        if player is None:
            raise HomeAssistantError(self._no_target_error)
        target = player.get("SteamID") or player.get("DisplayName")
        command = self._command_template.format(target=target)
        try:
            await self.coordinator.client.async_command(command)
        except RustRconError as err:
            raise HomeAssistantError(str(err)) from err
        await self.coordinator.async_request_refresh()


class RustKickPlayer(_RustPlayerActionButton):
    """Kick the player currently selected in select.target_player."""

    _attr_translation_key = "kick_player"
    _attr_icon = "mdi:account-remove"
    _attr_entity_category = EntityCategory.CONFIG
    _command_template = 'kick "{target}" "Kicked via Home Assistant"'

    def __init__(self, coordinator: RustRconCoordinator) -> None:
        super().__init__(coordinator, "kick_player")


class RustBanPlayer(_RustPlayerActionButton):
    """Ban the player currently selected in select.target_player."""

    _attr_translation_key = "ban_player"
    _attr_icon = "mdi:account-cancel"
    _attr_entity_category = EntityCategory.CONFIG
    _command_template = 'ban "{target}" "Banned via Home Assistant"'

    def __init__(self, coordinator: RustRconCoordinator) -> None:
        super().__init__(coordinator, "ban_player")
