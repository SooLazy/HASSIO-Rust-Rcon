"""Base entity."""
from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import RustRconCoordinator


class RustEntity(CoordinatorEntity[RustRconCoordinator]):
    """Shared naming: "<entity name> - <server name>", not grouped under a device.

    Home Assistant's registry always puts a device's name *before* the entity
    name for device-grouped entities, with no way to reverse that order. To
    get "<entity name> - <server name>" instead, these entities aren't
    attached to a device at all - the whole string is composed via
    translation placeholders (see strings.json) instead of device grouping.
    """

    _attr_has_entity_name = True

    def __init__(self, coordinator: RustRconCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        server_name = (coordinator.data or {}).get("Hostname") or entry.title
        self._attr_translation_placeholders = {"server_name": server_name}
