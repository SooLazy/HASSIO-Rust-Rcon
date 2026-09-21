"""Base entity."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RustRconCoordinator


class RustEntity(CoordinatorEntity[RustRconCoordinator]):
    """Shared device info / naming."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: RustRconCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Facepunch",
            model="Rust dedicated server",
        )
