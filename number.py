"""The Tesla Wall Charger Director integration."""
import asyncio
import logging

from homeassistant.components.number import NumberEntity

from twcdirector.listener import TWCListener
from twcdirector.device import TWCPeripheral, TWCController
from twcdirector.protocol import Commands

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .device import TWCDeviceEntity
from .const import (
    DOMAIN
)


_LOGGER = logging.getLogger(__name__)


async def new_number_processor(device_queue, hass, entry, async_add_entities):
    twc_listener: TWCListener = hass.data[DOMAIN][entry.entry_id]["twc_listener"]

    while True:
        new_device: TWCPeripheral = await device_queue.get()

        if isinstance(new_device, TWCPeripheral):
            _LOGGER.debug(f"Got new Tesla Wall Charger Device {new_device.get_address():04x}")
            endpoints = []

            default_current_endpoint = TWCDefaultCurrentEntity(new_device, twc_listener.get_fake_controller(), entry)
            endpoints.append(default_current_endpoint)
            device_registry = hass.helpers.device_registry.async_get(hass)
            device_info = default_current_endpoint.device_info
            device_info["config_entry_id"] = entry.entry_id
            device = device_registry.async_get_or_create(**device_info)
            _LOGGER.debug(f"Set Default Current Endpoint: {default_current_endpoint.entity_id} added")

            session_current_endpoint = TWCSessionCurrentEntity(new_device, twc_listener.get_fake_controller(), entry)
            endpoints.append(session_current_endpoint)
            device_registry = hass.helpers.device_registry.async_get(hass)
            device_info = session_current_endpoint.device_info
            device_info["config_entry_id"] = entry.entry_id
            device = device_registry.async_get_or_create(**device_info)
            _LOGGER.debug(f"Set Session Current Endpoint: {session_current_endpoint.entity_id} added")

            if endpoints:
                async_add_entities(endpoints)

        device_queue.task_done()


async def async_setup_platform(hass: HomeAssistant, entry: ConfigEntry, async_add_entities, discovery_info=None):
    """Set up the numnber platform."""
    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up TWCDevice from a config entry."""

    device_queue = asyncio.Queue()
    twc_listener = hass.data[DOMAIN][entry.entry_id]["twc_listener"]

    twc_listener.register_device_queue(device_queue)

    hass.loop.create_task(new_number_processor(device_queue, hass, entry, async_add_entities))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True


class TWCDefaultCurrentEntity(NumberEntity, TWCDeviceEntity):
    """Implementation of a Tesla Wall Charger Director Session Current Entity."""
    def __init__(self, twc_device: TWCPeripheral, twc_controller: TWCController, entry):
        """Initialize the sensor."""
        TWCDeviceEntity.__init__(self, twc_device)
        self._name = f"{self._twc_device.get_serial()} Default Current Setting"
        self._unique_id = f"{self._twc_device.get_serial()}_default_current_setting"
        self._config_entry = entry
        self._min_value = 0
        self._step = 1

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        await super().async_added_to_hass()

        state = await self.async_get_last_state()

        if state:
            self.set_native_value(float(state.state))

        self._twc_device.register_device_data_updated_callback({
            Commands.TWC_STATUS.name: self.async_write_ha_state,
            Commands.TWC_METER.name: self.async_write_ha_state,
        })

    async def async_will_remove_from_hass(self):
        """When entity will be removed from hass."""
        self._twc_device.deregister_device_data_updated_callback({
            Commands.TWC_STATUS.name: self.async_write_ha_state,
            Commands.TWC_METER.name: self.async_write_ha_state,
        })

    @property
    def native_min_value(self) -> float:
        return self._min_value

    @property
    def native_max_value(self) -> float:
        return self._twc_device.get_max_current() / 100

    @property
    def native_step(self) -> float:
        return self._step

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    def set_native_value(self, value: float) -> None:
        """Update the current value."""
        self._twc_device.set_setpoint_current(int(value * 100))

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        self._twc_device.set_setpoint_current(int(value * 100))

    @property
    def native_value(self) -> float:
        return self._twc_device.get_setpoint_current() / 100

    @property
    def native_unit_of_measurement(self):
        return "A"


class TWCSessionCurrentEntity(TWCDefaultCurrentEntity):
    def __init__(self, twc_device: TWCPeripheral, twc_controller: TWCController, entry):
        """Initialize the sensor."""
        super().__init__(twc_device, twc_controller, entry)
        self._twc_controller = twc_controller
        self._name = f"{self._twc_device.get_serial()} Session Current Setting"
        self._unique_id = f"{self._twc_device.get_serial()}_session_current_setting"

    def set_native_value(self, value: float) -> None:
        """Update the current value."""
        if value == 0:
            asyncio.create_task(self._twc_controller._event_loop.self._twc_controller.queue_peripheral_open_contactors_command(self._twc_device.get_address()))
        else:
            asyncio.create_task(self._twc_controller.queue_peripheral_close_contactors_command(self._twc_device.get_address()))
            asyncio.create_task(self._twc_controller.queue_peripheral_session_current_command(self._twc_device.get_address(), int(value * 100)))

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        if value == 0:
            await self._twc_controller.queue_peripheral_open_contactors_command(self._twc_device.get_address())
        else:
            await self._twc_controller.queue_peripheral_close_contactors_command(self._twc_device.get_address())
            await self._twc_controller.queue_peripheral_session_current_command(self._twc_device.get_address(), int(value * 100))

    @property
    def native_value(self) -> float:
        return self._twc_device.get_status_current_available() / 100

