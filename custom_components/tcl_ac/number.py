"""Number platform for TCL AC."""
import logging

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TCL AC number (timer) from a config entry."""
    name = config_entry.data.get(CONF_NAME)
    shared_data = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities([TclTimerNumber(name, config_entry.entry_id, shared_data)])


class TclTimerNumber(NumberEntity):
    """Timer Number Entity for TCL AC."""

    _attr_has_entity_name = True
    _attr_native_min_value = 0
    _attr_native_max_value = 24
    _attr_native_step = 1
    _attr_icon = "mdi:timer-outline"

    def __init__(self, ac_name, unique_id, shared_data):
        self._ac_name = ac_name
        self._attr_name = f"Timer {ac_name}"
        self._base_unique_id = unique_id
        self._attr_unique_id = f"{unique_id}_timer"
        self._shared_data = shared_data
        self._state = 0.0

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._base_unique_id)},
            name=self._ac_name,
            manufacturer="TCL",
            model="IR AC Blaster",
        )

    @property
    def native_value(self):
        """Return the current timer value."""
        return self._state

    async def async_set_native_value(self, value: float) -> None:
        """Set new timer value."""
        self._state = value
        self._shared_data["timer"] = int(value)
        self.async_write_ha_state()

        climate_entity = self._shared_data.get("climate_entity")
        if climate_entity:
            # Re-emit current air conditioner state with the new timer
            await climate_entity.async_send_command()
        else:
            _LOGGER.warning("Climate entity not found for timer command")
