"""The Tesla Wall Charger Director integration."""
import logging

import voluptuous as vol

from homeassistant.components.device_automation import TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import event as event_trigger
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_EVENT,
    CONF_PLATFORM,
    CONF_TYPE,
)

from .const import (
    DOMAIN,
    DOMAIN_EVENT
)

CONF_SUBTYPE = "subtype"

CONF_CONNECTED = "connected"
CONF_DISCONNECTED = "disconnected"

TWC_EVENT = {
    CONF_CONNECTED: {CONF_EVENT: "car_connected"},
    CONF_DISCONNECTED: {CONF_EVENT: "car_disconnected"},
}

TRIGGER_SCHEMA = TRIGGER_BASE_SCHEMA.extend(
    {vol.Required(CONF_TYPE): str}
)

_LOGGER = logging.getLogger(__name__)


async def async_get_triggers(hass, device_id):
    """Return a list of triggers."""

    triggers = []
    for trigger in TWC_EVENT:
        triggers.append(
            {
                CONF_DEVICE_ID: device_id,
                CONF_DOMAIN: DOMAIN,
                CONF_PLATFORM: "device",
                CONF_TYPE: trigger,
            }
        )

    return triggers


async def async_attach_trigger(hass, config, action, automation_info):
    """Attach a trigger."""
    config = TRIGGER_SCHEMA(config)

    trigger = config[CONF_TYPE]
    trigger = TWC_EVENT[trigger]

    event_config = {
        event_trigger.CONF_PLATFORM: "event",
        event_trigger.CONF_EVENT_TYPE: DOMAIN_EVENT,
        event_trigger.CONF_EVENT_DATA: {CONF_DEVICE_ID: config[CONF_DEVICE_ID], **trigger},
    }

    event_config = event_trigger.TRIGGER_SCHEMA(event_config)

    return await event_trigger.async_attach_trigger(
        hass, event_config, action, automation_info, platform_type="device"
    )
