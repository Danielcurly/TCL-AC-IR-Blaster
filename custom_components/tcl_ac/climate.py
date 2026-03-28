"""Climate platform for TCL AC."""
import logging
import json

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.climate.const import (
    FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH,
    PRESET_NONE, PRESET_ECO, PRESET_BOOST, PRESET_SLEEP,
    SWING_ON, SWING_OFF
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, CONF_DEVICE, CONF_SENSOR
from .tcl_protocol import generate_code

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TCL AC climate entities from a config entry."""
    name = config_entry.data.get(CONF_NAME)
    
    # Read from options if available, fallback to data
    device = config_entry.options.get(CONF_DEVICE, config_entry.data.get(CONF_DEVICE))
    sensor_id = config_entry.options.get(CONF_SENSOR, config_entry.data.get(CONF_SENSOR))

    topic = f"zigbee2mqtt/{device}/set"

    shared_data = hass.data[DOMAIN][config_entry.entry_id]

    climate_entity = TclClimate(hass, name, topic, sensor_id, config_entry.entry_id, shared_data)
    shared_data["climate_entity"] = climate_entity

    async_add_entities([climate_entity])


class TclClimate(ClimateEntity):
    """TCL AC Climate Entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_precision = 1.0

    def __init__(self, hass, name, topic, sensor_id, unique_id, shared_data):
        self.hass = hass
        self._name = name
        self._topic = topic
        self._sensor_id = sensor_id
        self._attr_unique_id = unique_id
        self._shared_data = shared_data

        self._hvac_mode = HVACMode.OFF
        self._target_temp = 24
        self._fan_mode = FAN_AUTO
        self._preset_mode = PRESET_NONE
        self._swing_mode = SWING_OFF
        self._current_temp = None

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        if self._sensor_id:
            async_track_state_change_event(
                self.hass, self._sensor_id, self._async_sensor_changed
            )
            sensor_state = self.hass.states.get(self._sensor_id)
            if sensor_state:
                self._update_current_temp(sensor_state)

    @property
    def name(self):
        return self._name

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=self._name,
            manufacturer="TCL",
            model="IR AC Blaster",
        )

    @property
    def temperature_unit(self):
        return UnitOfTemperature.CELSIUS

    @property
    def hvac_mode(self):
        return self._hvac_mode

    @property
    def hvac_modes(self):
        return [
            HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT,
            HVACMode.DRY, HVACMode.FAN_ONLY, HVACMode.HEAT_COOL,
        ]

    @property
    def fan_mode(self):
        return self._fan_mode

    @property
    def fan_modes(self):
        return [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]

    @property
    def preset_mode(self):
        return self._preset_mode

    @property
    def preset_modes(self):
        return [PRESET_NONE, PRESET_ECO, PRESET_BOOST, PRESET_SLEEP]

    @property
    def swing_mode(self):
        return self._swing_mode

    @property
    def swing_modes(self):
        return [SWING_OFF, SWING_ON]

    @property
    def target_temperature(self):
        return self._target_temp

    @property
    def current_temperature(self):
        return self._current_temp

    @property
    def target_temperature_step(self):
        return 1

    @property
    def min_temp(self):
        return 16

    @property
    def max_temp(self):
        return 30

    @property
    def supported_features(self):
        return (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.SWING_MODE
        )

    async def _async_sensor_changed(self, event):
        new_state = event.data.get("new_state")
        if new_state:
            self._update_current_temp(new_state)
            self.async_write_ha_state()

    def _update_current_temp(self, state):
        try:
            if state.state not in ("unknown", "unavailable"):
                self._current_temp = float(state.state)
        except (ValueError, TypeError):
            pass

    async def async_set_hvac_mode(self, hvac_mode):
        self._hvac_mode = hvac_mode
        await self.async_send_command()
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        if "temperature" in kwargs:
            self._target_temp = kwargs["temperature"]
            await self.async_send_command()
        self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode):
        self._fan_mode = fan_mode
        await self.async_send_command()
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode):
        self._preset_mode = preset_mode
        await self.async_send_command()
        self.async_write_ha_state()

    async def async_set_swing_mode(self, swing_mode):
        self._swing_mode = swing_mode
        await self.async_send_command()
        self.async_write_ha_state()

    async def async_send_command(self):
        power_off = self._hvac_mode == HVACMode.OFF

        mode_map = {
            HVACMode.HEAT: "heat",
            HVACMode.COOL: "cool",
            HVACMode.DRY: "dry",
            HVACMode.FAN_ONLY: "fan_only",
            HVACMode.HEAT_COOL: "auto",
        }
        
        tcl_mode = mode_map.get(self._hvac_mode, "cool")
        tcl_fan = self._fan_mode if self._fan_mode in ["auto", "low", "medium", "high"] else "auto"

        quiet = self._preset_mode == PRESET_SLEEP
        turbo = self._preset_mode == PRESET_BOOST
        eco = self._preset_mode == PRESET_ECO
        swing = self._swing_mode == SWING_ON
        timer_horas = int(self._shared_data.get("timer", 0))

        code = generate_code(
            mode=tcl_mode, 
            temp=int(self._target_temp), 
            speed=tcl_fan, 
            quiet=quiet, 
            turbo=turbo, 
            eco=eco, 
            swing=swing, 
            timer_horas=timer_horas, 
            power_off=power_off
        )
        
        payload = json.dumps({"ir_code_to_send": code})

        _LOGGER.debug("Sending TCL AC code to MQTT. Topic: %s", self._topic)
        
        await self.hass.services.async_call(
            domain="mqtt",
            service="publish",
            service_data={
                "topic": self._topic,
                "payload": payload,
            },
            blocking=False
        )
