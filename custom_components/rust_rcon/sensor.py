"""Sensors for Rust RCON."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import homeassistant.util.dt as dt_util
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfDataRate, UnitOfInformation, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import RustConfigEntry, RustRconCoordinator
from .entity import RustEntity


def _parse_save_time(data: dict[str, Any]) -> datetime | None:
    raw = data.get("SaveCreatedTime")
    return dt_util.parse_datetime(raw) if raw else None


@dataclass(frozen=True, kw_only=True)
class RustSensorDescription(SensorEntityDescription):
    """Sensor description with a value getter."""

    value_fn: Callable[[dict[str, Any]], Any]
    attrs_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


SENSORS: tuple[RustSensorDescription, ...] = (
    RustSensorDescription(
        key="hostname",
        translation_key="hostname",
        icon="mdi:server-network",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("Hostname"),
    ),
    RustSensorDescription(
        key="players",
        translation_key="players",
        icon="mdi:account-group",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("Players"),
        attrs_fn=lambda d: {
            "player_names": [
                p.get("DisplayName")
                for p in d.get("PlayerList", [])
                if p.get("DisplayName")
            ]
        },
    ),
    RustSensorDescription(
        key="max_players",
        translation_key="max_players",
        icon="mdi:account-multiple",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("MaxPlayers"),
    ),
    RustSensorDescription(
        key="queued",
        translation_key="queued",
        icon="mdi:account-clock",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("Queued"),
    ),
    RustSensorDescription(
        key="joining",
        translation_key="joining",
        icon="mdi:account-arrow-right",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("Joining"),
    ),
    RustSensorDescription(
        key="fps",
        translation_key="fps",
        icon="mdi:speedometer",
        native_unit_of_measurement="fps",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("Framerate"),
    ),
    RustSensorDescription(
        key="entities",
        translation_key="entities",
        icon="mdi:cube-outline",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("EntityCount"),
    ),
    RustSensorDescription(
        key="uptime",
        translation_key="uptime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("Uptime"),
    ),
    RustSensorDescription(
        key="map",
        translation_key="map",
        icon="mdi:map",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("Map"),
    ),
    RustSensorDescription(
        key="memory",
        translation_key="memory",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("Memory"),
    ),
    RustSensorDescription(
        key="network_in",
        translation_key="network_in",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("NetworkIn"),
    ),
    RustSensorDescription(
        key="network_out",
        translation_key="network_out",
        device_class=SensorDeviceClass.DATA_RATE,
        native_unit_of_measurement=UnitOfDataRate.BYTES_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("NetworkOut"),
    ),
    RustSensorDescription(
        key="save_created",
        translation_key="save_created",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_parse_save_time,
    ),
    RustSensorDescription(
        key="version",
        translation_key="version",
        icon="mdi:tag-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.get("Version"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: RustConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up sensors."""
    coordinator = entry.runtime_data
    async_add_entities(RustSensor(coordinator, desc) for desc in SENSORS)


class RustSensor(RustEntity, SensorEntity):
    """A Rust server sensor."""

    entity_description: RustSensorDescription

    def __init__(
        self, coordinator: RustRconCoordinator, description: RustSensorDescription
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self.coordinator.data or {})
