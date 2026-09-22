"""Binary sensors for Rust RCON."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import RustConfigEntry, RustRconCoordinator
from .entity import RustEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: RustConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([RustOnline(entry.runtime_data), RustRestarting(entry.runtime_data)])


class RustOnline(RustEntity, BinarySensorEntity):
    """On when the server answers RCON."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_translation_key = "online"

    def __init__(self, coordinator: RustRconCoordinator) -> None:
        super().__init__(coordinator, "online")

    @property
    def available(self) -> bool:
        return True  # "offline" is a valid state, not unavailable

    @property
    def is_on(self) -> bool:
        return self.coordinator.last_update_success


class RustRestarting(RustEntity, BinarySensorEntity):
    """On while the server is restarting."""

    _attr_translation_key = "restarting"
    _attr_icon = "mdi:restart-alert"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: RustRconCoordinator) -> None:
        super().__init__(coordinator, "restarting")

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data
        return bool(data.get("Restarting")) if data else None
