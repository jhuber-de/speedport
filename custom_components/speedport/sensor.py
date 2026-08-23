from dataclasses import dataclass
from datetime import datetime

from zoneinfo import ZoneInfo
from homeassistant.components.sensor import (
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfDataRate,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from speedport import Speedport

from custom_components.speedport import DOMAIN
from custom_components.speedport.device import SpeedportEntity


@dataclass
class SpeedportSensorEntityDescription(SensorEntityDescription):
    hybrid_only: bool = False


SENSORS: tuple[SpeedportSensorEntityDescription, ...] = (
    SpeedportSensorEntityDescription(
        key="public_ip_v4",
        name="IPv4",
        icon="mdi:earth",
    ),
    SpeedportSensorEntityDescription(
        key="public_ip_v6",
        name="IPv6",
        icon="mdi:earth",
    ),
    SpeedportSensorEntityDescription(
        key="inet_uptime",
        name="Internet Uptime",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SpeedportSensorEntityDescription(
        key="inet_upload",
        name="Upload",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfDataRate.BITS_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:upload",
    ),
    SpeedportSensorEntityDescription(
        key="inet_download",
        name="Download",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfDataRate.BITS_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:download",
    ),
    SpeedportSensorEntityDescription(
        key="dsl_upstream",
        name="DSL-Link Upstream",
        native_unit_of_measurement=UnitOfDataRate.BITS_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:upload",
    ),
    SpeedportSensorEntityDescription(
        key="dsl_downstream",
        name="DSL-Link Downstream",
        native_unit_of_measurement=UnitOfDataRate.BITS_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        icon="mdi:download",
    ),
    SpeedportSensorEntityDescription(
        key="router_state",
        name="Router State",
        icon="mdi:router-wireless",
    ),
    SpeedportSensorEntityDescription(
        key="dsl_pop",
        name="DSL-PoP",
        icon="mdi:map-marker-radius",
    ),
    SpeedportSensorEntityDescription(
        key="ex5g_signal_5g",
        name="5G Signal",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        icon="mdi:signal",
        hybrid_only=True,
    ),
    SpeedportSensorEntityDescription(
        key="ex5g_freq_5g",
        name="5G Frequency",
        icon="mdi:signal-5g",
        hybrid_only=True,
    ),
    SpeedportSensorEntityDescription(
        key="ex5g_signal_lte",
        name="LTE Signal",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        icon="mdi:signal",
        hybrid_only=True,
    ),
    SpeedportSensorEntityDescription(
        key="ex5g_freq_lte",
        name="LTE Frequency",
        icon="mdi:signal-4g",
        hybrid_only=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up entry."""
    speedport: Speedport = hass.data[DOMAIN][entry.entry_id]
    show_hybrid_sensors = entry.options.get("show_hybrid_sensors", True)

    entities = [
        SpeedportBinarySensor(hass, speedport, description)
        for description in SENSORS
        if not description.hybrid_only or show_hybrid_sensors
    ]

    async_add_entities(entities)


class SpeedportBinarySensor(SpeedportEntity, SensorEntity):
    entity_description: SpeedportSensorEntityDescription

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        if (data := self._speedport.get(self.entity_description.key)) is None:
            return None
        if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP:
            date = datetime.strptime(data, "%Y-%m-%d %H:%M:%S").replace(second=0)
            return date.replace(tzinfo=ZoneInfo("Europe/Berlin"))
        return data

    @property
    def available(self) -> bool:
        return (
            super().available
            and self._speedport.get(self.entity_description.key) is not None
        )
