"""Sensors for Rust RCON."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import RustConfigEntry, RustRconCoordinator
from .entity import RustEntity


@dataclass(frozen=True, kw_only=True)
class RustSensorDescription(SensorEntityDescription):
    """Sensor description with a value getter."""

    value_fn: Callable[[dict[str, Any]], Any]


SENSORS: tuple[RustSensorDescription, ...] = (
    RustSensorDescription(
        key="players",
        translation_key="players",
        name="Players",
        icon="mdi:account-group",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("Players"),
    ),
    RustSensorDescription(
        key="max_players",
        name="Max players",
        icon="mdi:account-multiple",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("MaxPlayers"),
    ),
    RustSensorDescription(
        key="queued",
        name="Queued players",
        icon="mdi:account-clock",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("Queued"),
    ),
    RustSensorDescription(
        key="joining",
        name="Joining players",
        icon="mdi:account-arrow-right",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("Joining"),
    ),
    RustSensorDescription(
        key="fps",
        name="Server FPS",
        icon="mdi:speedometer",
        native_unit_of_measurement="fps",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("Framerate"),
    ),
    RustSensorDescription(
        key="entities",
        name="Entities",
        icon="mdi:cube-outline",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("EntityCount"),
    ),
    RustSensorDescription(
        key="uptime",
        name="Uptime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("Uptime"),
    ),
    RustSensorDescription(
        key="map",
        name="Map",
        icon="mdi:map",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("Map"),
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
