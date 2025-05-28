"""Switch platform for GL.iNet integration."""
import logging
from typing import Any, Optional

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import GLiNetDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GL.iNet switches."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    # Create VPN switches for each configured VPN
    vpn_configs = coordinator.data.get("vpn_configs", [])
    for vpn_config in vpn_configs:
        entities.append(GLiNetVPNSwitch(coordinator, vpn_config, entry))
    
    async_add_entities(entities)


class GLiNetVPNSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a GL.iNet VPN switch."""

    def __init__(
        self,
        coordinator: GLiNetDataUpdateCoordinator,
        vpn_config: dict,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.vpn_config = vpn_config
        self.vpn_name = vpn_config.get("name", "Unknown VPN")
        self.vpn_type = vpn_config.get("type", "unknown")
        
        self._attr_name = f"VPN {self.vpn_name}"
        self._attr_unique_id = f"{entry.entry_id}_vpn_{self.vpn_name.lower().replace(' ', '_')}"
        self._attr_icon = "mdi:vpn"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": MANUFACTURER,
            "model": coordinator.data.get("system_info", {}).get("model", "Unknown"),
            "sw_version": coordinator.data.get("system_info", {}).get("firmware_version", "Unknown"),
        }

    @property
    def is_on(self) -> bool:
        """Return true if the VPN is connected."""
        vpn_status = self.coordinator.data.get("vpn_status", {})
        active_vpn_name = vpn_status.get("name")
        
        if vpn_status.get("status") == 1 and active_vpn_name:
            # Check if this VPN is the active one
            return self.vpn_name in active_vpn_name or active_vpn_name in self.vpn_name
        
        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "vpn_type": self.vpn_type.upper(),
            "group_id": self.vpn_config.get("group_id"),
            "group_name": self.vpn_config.get("group_name"),
            "client_id": self.vpn_config.get("client_id"),
            "peer_id": self.vpn_config.get("peer_id"),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the VPN."""
        _LOGGER.debug("Starting VPN: %s", self.vpn_name)
        success = await self.coordinator.async_start_vpn(self.vpn_name)
        if not success:
            _LOGGER.error("Failed to start VPN: %s", self.vpn_name)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the VPN."""
        _LOGGER.debug("Stopping VPN: %s", self.vpn_name)
        success = await self.coordinator.async_stop_vpn(self.vpn_name)
        if not success:
            _LOGGER.error("Failed to stop VPN: %s", self.vpn_name)
