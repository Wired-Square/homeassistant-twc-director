"""The Tesla Wall Charger Director integration."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_EVENT, CONF_ID, CONF_DEVICE_ID

from twcdirector.device import TWCPeripheral

from .const import (
    DOMAIN_EVENT
)

from .device import (
    TWCDeviceEntity
)

_LOGGER = logging.getLogger(__name__)


class TWCDeviceEvent(TWCDeviceEntity):
    def __init__(self, hass: HomeAssistant, twc_device: TWCPeripheral):
        super().__init__(twc_device)
        self.hass = hass
        self._name = self._device_name

        self._twc_device.register_device_data_updated_callback({
            "TWC_CAR_CONNECTED": self._connected_event
        })

    async def _connected_event(self):
        event_data = {
            CONF_ID: self.unique_id,
            CONF_DEVICE_ID: self.entity_id,
            CONF_EVENT: "car_connected" if self._twc_device.is_car_connected() else "car_disconnected"
        }

        self.hass.bus.async_fire(DOMAIN_EVENT, event_data)
