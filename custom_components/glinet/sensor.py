"""Sensor platform for GL.iNet integration."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import GLiNetDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTIONS = [
    SensorEntityDescription(
        key="vpn_status",
        name="VPN Status",
        icon="mdi:vpn",
    ),
    SensorEntityDescription(
        key="system_status",
        name="System Status",
        icon="mdi:router-wireless",
    ),
    SensorEntityDescription(
        key="system_info",
        name="System Info",
        icon="mdi:information",
    ),
    SensorEntityDescription(
        key="disk_info",
        name="Disk Info",
        icon="mdi:harddisk",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GL.iNet sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    for description in SENSOR_DESCRIPTIONS:
        entities.append(GLiNetSensor(coordinator, description, entry))
    
    async_add_entities(entities)


class GLiNetSensor(CoordinatorEntity, SensorEntity):
    """Representation of a GL.iNet sensor."""

    def __init__(
        self,
        coordinator: GLiNetDataUpdateCoordinator,
        description: SensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": MANUFACTURER,
            "model": coordinator.data.get("system_info", {}).get("model", "Unknown"),
            "sw_version": coordinator.data.get("system_info", {}).get("firmware_version", "Unknown"),
        }

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        data = self.coordinator.data.get(self.entity_description.key, {})
        
        if self.entity_description.key == "vpn_status":
            if data.get("status") == 1:
                return "Connected"
            return "Disconnected"
        elif self.entity_description.key in ["system_status", "system_info", "disk_info"]:
            return "OK" if data else "Error"
        
        return "Unknown"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        data = self.coordinator.data.get(self.entity_description.key, {})
        
        if self.entity_description.key == "vpn_status":
            return {
                "name": data.get("name"),
                "ipv4": data.get("ipv4"),
                "domain": data.get("domain"),
                "rx_bytes": data.get("rx_bytes"),
                "tx_bytes": data.get("tx_bytes"),
                "group_id": data.get("group_id"),
                "client_id": data.get("client_id"),
                "peer_id": data.get("peer_id"),
            }
        elif self.entity_description.key == "system_status":
            return {
                "network": data.get("network"),
                "wifi": data.get("wifi"),
                "service": data.get("service"),
                "client": data.get("client"),
                "system": data.get("system"),
            }
        elif self.entity_description.key == "system_info":
            return {
                "mac": data.get("mac"),
                "model": data.get("model"),
                "firmware_version": data.get("firmware_version"),
                "firmware_date": data.get("firmware_date"),
                "hardware_version": data.get("hardware_version"),
                "vendor": data.get("vendor"),
                "sn": data.get("sn"),
                "cpu_num": data.get("cpu_num"),
                "country_code": data.get("country_code"),
            }
        elif self.entity_description.key == "disk_info":
            return {
                "root": data.get("root"),
                "tmp": data.get("tmp"),
            }
        
        return {}

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
