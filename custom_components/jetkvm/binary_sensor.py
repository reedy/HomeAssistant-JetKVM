"""Binary sensor platform for JetKVM integration.

Exposes boolean states from the JetKVM native Prometheus metrics:
  - Cloud connection status
  - Time synchronization status

These are only available when a password is configured (the /metrics
endpoint on port 80 requires authentication).
"""
import logging
from dataclasses import dataclass
from typing import List

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import JetKVMCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class JetKVMBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a JetKVM binary sensor."""


BINARY_SENSOR_DESCRIPTIONS: List[JetKVMBinarySensorDescription] = [
    JetKVMBinarySensorDescription(
        key="cloud_connected",
        translation_key="cloud_connected",
        icon="mdi:cloud-check-outline",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    JetKVMBinarySensorDescription(
        key="timesync_ok",
        translation_key="time_synced",
        icon="mdi:clock-check-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up JetKVM binary sensors from a config entry."""
    coordinator: JetKVMCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities(
        JetKVMBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class JetKVMBinarySensor(CoordinatorEntity[JetKVMCoordinator], BinarySensorEntity):
    """Representation of a JetKVM binary sensor."""

    _attr_has_entity_name = True
    entity_description: JetKVMBinarySensorDescription

    def __init__(
        self,
        coordinator: JetKVMCoordinator,
        entry: ConfigEntry,
        description: JetKVMBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._entry = entry

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.coordinator.data is None:
            return None
        value = self.coordinator.data.get(self.entity_description.key)
        if value is None:
            return None
        return bool(value)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info to link this entity to the device registry."""
        data = self._entry.data
        serial = data.get("serial_number", "")

        identifiers = set()
        if serial:
            identifiers.add((DOMAIN, serial))
        else:
            identifiers.add((DOMAIN, self._entry.entry_id))

        return DeviceInfo(identifiers=identifiers)

