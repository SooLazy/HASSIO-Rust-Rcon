"""A free-form RCON console."""
from __future__ import annotations

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import RustConfigEntry, RustRconCoordinator
from .entity import RustEntity
from .rcon import RustRconError

MAX_RESPONSE_LENGTH = 2000


async def async_setup_entry(
    hass: HomeAssistant, entry: RustConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([RustConsole(entry.runtime_data)])


class RustConsole(RustEntity, TextEntity):
    """Send an arbitrary RCON command; the reply is exposed as an attribute."""

    _attr_translation_key = "console"
    _attr_icon = "mdi:console"
    _attr_mode = TextMode.TEXT

    def __init__(self, coordinator: RustRconCoordinator) -> None:
        super().__init__(coordinator, "console")
        self._attr_native_value = ""
        self._response: str | None = None

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        if self._response is None:
            return None
        return {"response": self._response}

    async def async_set_value(self, value: str) -> None:
        try:
            response = await self.coordinator.client.async_command(value)
        except RustRconError as err:
            raise HomeAssistantError(str(err)) from err
        self._attr_native_value = value
        self._response = (response or "(no output)")[:MAX_RESPONSE_LENGTH]
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
