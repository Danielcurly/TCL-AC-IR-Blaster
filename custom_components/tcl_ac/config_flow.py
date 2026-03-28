"""Config flow for TCL AC integration."""
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_NAME

from .const import DOMAIN, CONF_DEVICE, CONF_SENSOR, DEFAULT_NAME


class TclAcConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TCL AC."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return TclAcOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_NAME])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_DEVICE): str,
                vol.Optional(CONF_SENSOR): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={},
        )


class TclAcOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a options flow for TCL AC."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_DEVICE,
                        default=self.config_entry.options.get(
                            CONF_DEVICE, self.config_entry.data.get(CONF_DEVICE)
                        ),
                    ): str,
                    vol.Optional(
                        CONF_SENSOR,
                        default=self.config_entry.options.get(
                            CONF_SENSOR, self.config_entry.data.get(CONF_SENSOR)
                        ),
                    ): str,
                }
            ),
        )
