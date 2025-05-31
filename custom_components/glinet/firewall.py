"""Firewall management for GL.iNet routers."""
import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import GLiNetDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class GLiNetDMZSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of GL.iNet DMZ switch."""

    def __init__(self, coordinator: GLiNetDataUpdateCoordinator) -> None:
        """Initialize the DMZ switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_dmz"
        self._attr_name = f"{coordinator.config_entry.title} DMZ"
        self._attr_icon = "mdi:shield-off"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": coordinator.config_entry.title,
            "manufacturer": MANUFACTURER,
            "model": coordinator.data.get("system_info", {}).get("model", "Unknown"),
            "sw_version": coordinator.data.get("system_info", {}).get("firmware_version", "Unknown"),
        }

    @property
    def is_on(self) -> bool:
        """Return true if DMZ is enabled."""
        dmz_config = self.coordinator.data.get("dmz", {})
        return dmz_config.get("enabled", False)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        dmz_config = self.coordinator.data.get("dmz", {})
        return {
            "destination_ip": dmz_config.get("dest_ip"),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on DMZ."""
        # This would need to be configured with a destination IP
        _LOGGER.warning("DMZ cannot be enabled without a destination IP. Use the service to configure.")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off DMZ."""
        await self.hass.async_add_executor_job(
            self.coordinator.api.set_dmz_config, False
        )
        await self.coordinator.async_request_refresh()


class GLiNetWANAccessSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of GL.iNet WAN access switches."""

    def __init__(self, coordinator: GLiNetDataUpdateCoordinator, access_type: str, name: str) -> None:
        """Initialize the WAN access switch."""
        super().__init__(coordinator)
        self.access_type = access_type
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_wan_{access_type}"
        self._attr_name = f"{coordinator.config_entry.title} {name}"
        self._attr_icon = self._get_icon()
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": coordinator.config_entry.title,
            "manufacturer": MANUFACTURER,
            "model": coordinator.data.get("system_info", {}).get("model", "Unknown"),
            "sw_version": coordinator.data.get("system_info", {}).get("firmware_version", "Unknown"),
        }

    def _get_icon(self) -> str:
        """Get icon based on access type."""
        icons = {
            "ping": "mdi:access-point-network",
            "https": "mdi:web",
            "ssh": "mdi:console-network",
        }
        return icons.get(self.access_type, "mdi:network")

    @property
    def is_on(self) -> bool:
        """Return true if WAN access is enabled."""
        wan_access = self.coordinator.data.get("wan_access", {})
        return wan_access.get(f"enable_{self.access_type}", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on WAN access."""
        wan_access = self.coordinator.data.get("wan_access", {})
        config = {
            f"enable_{self.access_type}": True,
            # Preserve other settings
            "enable_ping": wan_access.get("enable_ping", False),
            "enable_https": wan_access.get("enable_https", False),
            "enable_ssh": wan_access.get("enable_ssh", False),
        }
        config[f"enable_{self.access_type}"] = True
        
        await self.hass.async_add_executor_job(
            self.coordinator.api.set_wan_access, config
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off WAN access."""
        wan_access = self.coordinator.data.get("wan_access", {})
        config = {
            f"enable_{self.access_type}": False,
            # Preserve other settings
            "enable_ping": wan_access.get("enable_ping", False),
            "enable_https": wan_access.get("enable_https", False),
            "enable_ssh": wan_access.get("enable_ssh", False),
        }
        config[f"enable_{self.access_type}"] = False
        
        await self.hass.async_add_executor_job(
            self.coordinator.api.set_wan_access, config
        )
        await self.coordinator.async_request_refresh()


async def register_firewall_services(hass: HomeAssistant, coordinator: GLiNetDataUpdateCoordinator) -> None:
    """Register firewall-related services."""
    
    async def handle_add_firewall_rule(call: ServiceCall) -> None:
        """Handle add firewall rule service."""
        rule_params = {
            "name": call.data.get("name"),
            "src": call.data.get("src"),
            "src_ip": call.data.get("src_ip"),
            "src_mac": call.data.get("src_mac"),
            "src_port": call.data.get("src_port"),
            "proto": call.data.get("proto"),
            "dest": call.data.get("dest"),
            "dest_ip": call.data.get("dest_ip"),
            "dest_port": call.data.get("dest_port"),
            "enabled": call.data.get("enabled", True),
            "target": call.data["target"],
        }
        # Remove None values
        rule_params = {k: v for k, v in rule_params.items() if v is not None}
        
        result = await hass.async_add_executor_job(
            coordinator.api.add_firewall_rule, rule_params
        )
        if result:
            await coordinator.async_request_refresh()
            _LOGGER.info("Added firewall rule: %s", result)
        else:
            _LOGGER.error("Failed to add firewall rule")

    async def handle_remove_firewall_rule(call: ServiceCall) -> None:
        """Handle remove firewall rule service."""
        rule_id = call.data.get("rule_id")
        remove_all = call.data.get("remove_all", False)
        
        result = await hass.async_add_executor_job(
            coordinator.api.remove_firewall_rule, rule_id, remove_all
        )
        if result is not None:
            await coordinator.async_request_refresh()
            _LOGGER.info("Removed firewall rule(s)")
        else:
            _LOGGER.error("Failed to remove firewall rule")

    async def handle_add_port_forward(call: ServiceCall) -> None:
        """Handle add port forward service."""
        forward_params = {
            "name": call.data.get("name"),
            "proto": call.data.get("proto"),
            "src": call.data["src"],
            "src_dport": call.data["src_dport"],
            "dest": call.data["dest"],
            "dest_ip": call.data["dest_ip"],
            "dest_port": call.data["dest_port"],
            "enabled": call.data.get("enabled", True),
        }
        # Remove None values
        forward_params = {k: v for k, v in forward_params.items() if v is not None}
        
        result = await hass.async_add_executor_job(
            coordinator.api.add_port_forward, forward_params
        )
        if result:
            await coordinator.async_request_refresh()
            _LOGGER.info("Added port forward: %s", result)
        else:
            _LOGGER.error("Failed to add port forward")

    async def handle_remove_port_forward(call: ServiceCall) -> None:
        """Handle remove port forward service."""
        rule_id = call.data.get("rule_id")
        remove_all = call.data.get("remove_all", False)
        
        result = await hass.async_add_executor_job(
            coordinator.api.remove_port_forward, rule_id, remove_all
        )
        if result is not None:
            await coordinator.async_request_refresh()
            _LOGGER.info("Removed port forward(s)")
        else:
            _LOGGER.error("Failed to remove port forward")

    async def handle_set_dmz(call: ServiceCall) -> None:
        """Handle set DMZ service."""
        enabled = call.data["enabled"]
        dest_ip = call.data.get("dest_ip")
        
        result = await hass.async_add_executor_job(
            coordinator.api.set_dmz_config, enabled, dest_ip
        )
        if result is not None:
            await coordinator.async_request_refresh()
            _LOGGER.info("Set DMZ configuration")
        else:
            _LOGGER.error("Failed to set DMZ configuration")

    # Register services
    hass.services.async_register(DOMAIN, "add_firewall_rule", handle_add_firewall_rule)
    hass.services.async_register(DOMAIN, "remove_firewall_rule", handle_remove_firewall_rule)
    hass.services.async_register(DOMAIN, "add_port_forward", handle_add_port_forward)
    hass.services.async_register(DOMAIN, "remove_port_forward", handle_remove_port_forward)
    hass.services.async_register(DOMAIN, "set_dmz", handle_set_dmz)
