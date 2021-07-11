"""Config flow for Tesla Wall Charger Director."""
import logging

import voluptuous as vol

from homeassistant import config_entries

from .const import (
    DOMAIN,
    CONF_RS485_INTERFACE,
    CONF_SHARED_MAX_CURRENT,
)

_LOGGER = logging.getLogger(__name__)


class TWCFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Tesla Wall Charger Director config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    def __init__(self):
        """Initialize Tesla Wall Charger Director ConfigFlow."""
        self.rs485_interface = "ttyUSB0"
        self.shared_max_current = 3200

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            if _device_already_added(self._async_current_entries(), user_input[CONF_RS485_INTERFACE]):
                return self.async_abort(reason="already_configured")

            self.rs485_interface = user_input[CONF_RS485_INTERFACE]
            return self.async_create_entry(
                title=self.rs485_interface, data={CONF_RS485_INTERFACE: self.rs485_interface,
                                                  CONF_SHARED_MAX_CURRENT: self.shared_max_current}
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_RS485_INTERFACE): vol.In(["ttyUSB0", "ttyUSB1", "ttySC0", "ttySC1"]),
                    vol.Required(CONF_SHARED_MAX_CURRENT, default=3200): int,
                }
            ),
        )


def _device_already_added(current_entries, rs485_interface):
    """Determine if entry has already been added to HA."""
    for entry in current_entries:
        entry_rs485_interface = entry.data.get(CONF_RS485_INTERFACE)

        if entry_rs485_interface == rs485_interface:
            return True

    return False
