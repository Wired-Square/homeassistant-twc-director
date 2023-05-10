import asyncio
import logging

from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_FRIENDLY_NAME,
    CONF_UNIT_OF_MEASUREMENT,
    DEVICE_CLASS_ENERGY,
    ENERGY_KILO_WATT_HOUR,
)

from homeassistant.components.sensor import (
    ATTR_STATE_CLASS,
    STATE_CLASS_MEASUREMENT,
    STATE_CLASS_TOTAL_INCREASING,
)

from twcdirector.device import TWCPeripheral
from twcdirector.protocol import Commands, Status

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .device import TWCDeviceEntity
from .const import (
    DOMAIN,
    CONF_SCALE,
    CONF_ROUND,
    CONF_FORMAT
)

_LOGGER = logging.getLogger(__name__)


SENSOR_TYPES = {
    "total_kwh": {
        CONF_FRIENDLY_NAME: "Total Energy Delivered",
        CONF_DEVICE_CLASS: DEVICE_CLASS_ENERGY,
        CONF_SCALE: 1,
        CONF_UNIT_OF_MEASUREMENT: ENERGY_KILO_WATT_HOUR,
        ATTR_STATE_CLASS: STATE_CLASS_TOTAL_INCREASING
    },
    "voltage_phase_l1": {
        CONF_FRIENDLY_NAME: "AC Voltage Phase 1",
        CONF_DEVICE_CLASS: "voltage",
        CONF_SCALE: 1,
        CONF_UNIT_OF_MEASUREMENT: "V"
    },
    "voltage_phase_l2": {
        CONF_FRIENDLY_NAME: "AC Voltage Phase 2",
        CONF_DEVICE_CLASS: "voltage",
        CONF_SCALE: 1,
        CONF_UNIT_OF_MEASUREMENT: "V"
    },
    "voltage_phase_l3": {
        CONF_FRIENDLY_NAME: "AC Voltage Phase 3",
        CONF_DEVICE_CLASS: "voltage",
        CONF_SCALE: 1,
        CONF_UNIT_OF_MEASUREMENT: "V"
    },
    "current_phase_l1": {
        CONF_FRIENDLY_NAME: "AC Current Phase 1",
        CONF_DEVICE_CLASS: "current",
        CONF_SCALE: 1,
        CONF_UNIT_OF_MEASUREMENT: "A"
    },
    "current_phase_l2": {
        CONF_FRIENDLY_NAME: "AC Current Phase 2",
        CONF_DEVICE_CLASS: "current",
        CONF_SCALE: 1,
        CONF_UNIT_OF_MEASUREMENT: "A"
    },
    "current_phase_l3": {
        CONF_FRIENDLY_NAME: "AC Current Phase 3",
        CONF_DEVICE_CLASS: "current",
        CONF_SCALE: 1,
        CONF_UNIT_OF_MEASUREMENT: "A"
    },
    "charge_state": {
        CONF_FRIENDLY_NAME: "TWC Status",
        CONF_DEVICE_CLASS: f"{DOMAIN}__twc_status",
        CONF_SCALE: 1,
        CONF_UNIT_OF_MEASUREMENT: ""
    },
    "current_available": {
        CONF_FRIENDLY_NAME: "Charge Current Set",
        CONF_DEVICE_CLASS: "current",
        CONF_SCALE: 0.01,
        CONF_UNIT_OF_MEASUREMENT: "A",
        CONF_ROUND: 2,
        CONF_FORMAT: ".02f"
    },
    "current_delivered": {
        CONF_FRIENDLY_NAME: "Charge Current Delivered",
        CONF_DEVICE_CLASS: "current",
        CONF_SCALE: 0.01,
        CONF_UNIT_OF_MEASUREMENT: "A",
        CONF_ROUND: 2,
        CONF_FORMAT: ".02f"
    },
    "vin": {
        CONF_FRIENDLY_NAME: "Vehicle VIN",
        CONF_DEVICE_CLASS: None,
        CONF_UNIT_OF_MEASUREMENT: None
    }
}


async def new_sensor_processor(device_queue, hass, entry, async_add_entities):
    while True:
        new_device: TWCPeripheral = await device_queue.get()

        if isinstance(new_device, TWCPeripheral):
            _LOGGER.debug(f"Got new Tesla Wall Charger Device {new_device.get_address():04x}")
            sensors = []

            for (entity_attribute, entity_detail) in SENSOR_TYPES.items():
                sensor = TWCStateSensor(new_device, entry, entity_attribute, entity_detail)
                sensors.append(sensor)
                device_registry = hass.helpers.device_registry.async_get(hass)
                device_info = sensor.device_info
                device_info["config_entry_id"] = entry.entry_id
                device = device_registry.async_get_or_create(**device_info)
                _LOGGER.debug(f"Sensor: {sensor.entity_id} added")

            if sensors:
                async_add_entities(sensors)

        device_queue.task_done()


async def async_setup_platform(hass: HomeAssistant, entry: ConfigEntry, async_add_entities, discovery_info=None):
    """Set up the sensor platform."""
    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up Tesla Wall Charger Director from a config entry."""

    device_queue = asyncio.Queue()
    twc_listener = hass.data[DOMAIN][entry.entry_id]["twc_listener"]

    twc_listener.register_device_queue(device_queue)

    hass.loop.create_task(new_sensor_processor(device_queue, hass, entry, async_add_entities))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True


class TWCStateSensor(TWCDeviceEntity):
    """Implementation of a Tesla Wall Charger Director Sensor."""
    def __init__(self, twc_device: TWCPeripheral, entry, entity_attribute, entity_detail):
        """Initialize the sensor."""
        super().__init__(twc_device)
        self._entity_attribute = entity_attribute
        self._entity_detail = entity_detail
        self._unit_of_measure = entity_detail[CONF_UNIT_OF_MEASUREMENT]
        self._state_class = entity_detail.get(ATTR_STATE_CLASS, None)
        self._round = entity_detail.get(CONF_ROUND, None)
        self._format = entity_detail.get(CONF_FORMAT, None)
        self._scale = entity_detail.get(CONF_SCALE, None)
        self._name = f"{self._twc_device.get_serial()} {self._entity_detail[CONF_FRIENDLY_NAME]}"
        self._unique_id = f"{self._twc_device.get_serial()}_{self._entity_attribute}"
        self._config_entry = entry
        self._device_class = self._entity_detail[CONF_DEVICE_CLASS]

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        await super().async_added_to_hass()
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
    def device_class(self):
        return self._device_class

    @property
    def state_class(self):
        return self._state_class

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

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._entity_attribute == "vin":
            self._state = self._twc_device.get_vin()
        elif self._entity_attribute == "charge_state":
            self._state = Status(self._twc_device.get_device_data().get(self._entity_attribute, 0)).name
        else:
            self._state = self._twc_device.get_device_data().get(self._entity_attribute, 0) * self._scale

            if self._round:
                self._state = round(self._state, self._round)

        if self._format:
            return f"{self._state:{self._format}}"
        else:
            return self._state

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def unit_of_measurement(self):
        return  self._unit_of_measure

