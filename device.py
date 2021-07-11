"""The Tesla Wall Charger Director integration."""
import logging

from homeassistant.helpers.restore_state import RestoreEntity

from twcdirector.device import TWCPeripheral
from twcdirector.protocol import Commands

from .const import DEFAULT_NAME
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)


class TWCDeviceEntity(RestoreEntity):
    def __init__(self, twc_device: TWCPeripheral):
        super().__init__()
        self._twc_device: TWCPeripheral = twc_device
        self._address = self._twc_device.get_address()
        self._device_name = f"{self._twc_device.get_serial()} {self._address:04X}"
        self._device_id = f"{self._twc_device.get_serial()}_{self._address:04X}"
        self._attributes = {"address": f"{self._address:04x}"}

    @property
    def device_info(self):
        """Return the device_info of the device."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._device_name,
            "manufacturer": DEFAULT_NAME,
            "sw_version": self._twc_device.get_version(),
            "model": "Tesla Wall Charger",
            "via_device": (DOMAIN, self._device_id),
        }

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        self._attributes["Restart Count"] = f"{self._twc_device.get_restart_counter()}"
        return self._attributes

    @property
    def name(self):
        """Return the name of the entity."""
        return self._device_name

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self._twc_device.register_device_data_updated_callback({
            Commands.TWC_PERIPHERAL.name: self.async_write_ha_state,
        })

    async def async_will_remove_from_hass(self):
        """When entity will be removed from hass."""
        self._twc_device.deregister_device_data_updated_callback({
            Commands.TWC_PERIPHERAL.name: self.async_write_ha_state,
        })

    @property
    def should_poll(self) -> bool:
        return False
