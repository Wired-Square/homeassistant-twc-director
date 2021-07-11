"""The Tesla Wall Charger Director integration."""
import asyncio

from twcdirector.listener import TWCListener
from twcdirector.device import TWCPeripheral

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import (EVENT_HOMEASSISTANT_STOP)

from .const import (
    DOMAIN,
    CONF_RS485_INTERFACE,
    CONF_SHARED_MAX_CURRENT
)

from .event import (
    TWCDeviceEvent
)

import logging

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "number"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Tesla Wall Charger Director component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Tesla Wall Charger Director from a config entry."""

    listener_config = entry.data

    listener_options = {
        "event_loop": hass.loop
    }

    if CONF_RS485_INTERFACE in listener_config:
        listener_options["interface"] = f"/dev/{listener_config[CONF_RS485_INTERFACE]}"
    if CONF_SHARED_MAX_CURRENT in listener_config:
        listener_options["shared_max_current"] = listener_config[CONF_SHARED_MAX_CURRENT]

    twc_listener = TWCListener(**listener_options)

    hass.loop.create_task(twc_listener.process_transmit_messages())
    hass.loop.create_task(twc_listener.listen())

    # Shutdown event closure
    async def async_shutdown_event(call):
        _LOGGER.info("Shutting down Tesla Wall Charger Director")
        await twc_listener.shutdown()

    hass.bus.async_listen(EVENT_HOMEASSISTANT_STOP, async_shutdown_event)

    hass.data[DOMAIN].setdefault(entry.entry_id, {})
    hass.data[DOMAIN][entry.entry_id]["twc_listener"] = twc_listener

    device_queue = asyncio.Queue()

    twc_listener.register_device_queue(device_queue)

    hass.loop.create_task(new_device_processor(device_queue, hass, entry))

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(await asyncio.gather(*[
        hass.config_entries.async_forward_entry_unload(entry, component)
        for component in PLATFORMS
    ]))

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def new_device_processor(device_queue, hass, entry):
    while True:
        new_device = await device_queue.get()

        if isinstance(new_device, TWCPeripheral):
            event_entity = TWCDeviceEvent(hass, new_device)
            device_registry = await hass.helpers.device_registry.async_get_registry()
            device_info = event_entity.device_info
            device_info["config_entry_id"] = entry.entry_id
            device = device_registry.async_get_or_create(**device_info)
            event_entity.entity_id = device.id
            _LOGGER.debug(f"Trigger Device Info: {device_info}")

        device_queue.task_done()
