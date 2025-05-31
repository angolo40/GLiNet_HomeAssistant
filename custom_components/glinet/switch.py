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
from .firewall import GLiNetDMZSwitch, GLiNetWANAccessSwitch, register_firewall_services

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
    
    # Add firewall switches
    # DMZ switch
    entities.append(GLiNetDMZSwitch(coordinator))
    
    # WAN access switches
    entities.extend([
        GLiNetWANAccessSwitch(coordinator, "ping", "WAN Ping"),
        GLiNetWANAccessSwitch(coordinator, "https", "WAN HTTPS Access"),
        GLiNetWANAccessSwitch(coordinator, "ssh", "WAN SSH Access"),
    ])
    
    # VPN Server switches
    entities.append(GLiNetWireGuardServerSwitch(coordinator, entry))
    entities.append(GLiNetOpenVPNServerSwitch(coordinator, entry))
    
    # WiFi switches
    wifi_config = coordinator.data.get("wifi_config", {})
    for device_config in wifi_config.get("res", []):
        for iface in device_config.get("ifaces", []):
            entities.append(GLiNetWiFiSwitch(coordinator, iface, device_config, entry))
    
    async_add_entities(entities)
    
    # Register firewall services
    await register_firewall_services(hass, coordinator)


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


class GLiNetWireGuardServerSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a GL.iNet WireGuard Server switch."""

    def __init__(
        self,
        coordinator: GLiNetDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        
        self._attr_name = "WireGuard Server"
        self._attr_unique_id = f"{entry.entry_id}_wg_server"
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
        """Return true if the WireGuard server is running."""
        wg_status = self.coordinator.data.get("wg_server_status", {})
        server_info = wg_status.get("server", {})
        return server_info.get("status", 0) == 1

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        wg_status = self.coordinator.data.get("wg_server_status", {})
        wg_config = self.coordinator.data.get("wg_server_config", {})
        server_info = wg_status.get("server", {})
        
        attrs = {
            "initialization": server_info.get("initialization", False),
            "tunnel_ip": server_info.get("tunnel_ip"),
            "rx_bytes": server_info.get("rx_bytes"),
            "tx_bytes": server_info.get("tx_bytes"),
            "port": wg_config.get("port"),
            "public_key": wg_config.get("public_key"),
            "ipv6_enabled": wg_config.get("ipv6_enable", False),
        }
        
        # Add peer information
        peers = wg_status.get("peers", [])
        attrs["connected_peers"] = len([p for p in peers if p.get("status") == 1])
        attrs["total_peers"] = len(peers)
        
        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the WireGuard server."""
        _LOGGER.debug("Starting WireGuard server")
        success = await self.coordinator.async_start_wg_server()
        if not success:
            _LOGGER.error("Failed to start WireGuard server")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the WireGuard server."""
        _LOGGER.debug("Stopping WireGuard server")
        success = await self.coordinator.async_stop_wg_server()
        if not success:
            _LOGGER.error("Failed to stop WireGuard server")


class GLiNetOpenVPNServerSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a GL.iNet OpenVPN Server switch."""

    def __init__(
        self,
        coordinator: GLiNetDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        
        self._attr_name = "OpenVPN Server"
        self._attr_unique_id = f"{entry.entry_id}_ovpn_server"
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
        """Return true if the OpenVPN server is running."""
        ovpn_status = self.coordinator.data.get("ovpn_server_status", {})
        return ovpn_status.get("status", 0) == 1

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        ovpn_status = self.coordinator.data.get("ovpn_server_status", {})
        
        return {
            "initialization": ovpn_status.get("initialization", False),
            "tunnel_ip": ovpn_status.get("tunnel_ip"),
            "rx_bytes": ovpn_status.get("rx_bytes"),
            "tx_bytes": ovpn_status.get("tx_bytes"),
            "log": ovpn_status.get("log"),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the OpenVPN server."""
        _LOGGER.debug("Starting OpenVPN server")
        success = await self.coordinator.async_start_ovpn_server()
        if not success:
            _LOGGER.error("Failed to start OpenVPN server")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the OpenVPN server."""
        _LOGGER.debug("Stopping OpenVPN server")
        success = await self.coordinator.async_stop_ovpn_server()
        if not success:
            _LOGGER.error("Failed to stop OpenVPN server")


class GLiNetWiFiSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a GL.iNet WiFi switch."""

    def __init__(
        self,
        coordinator: GLiNetDataUpdateCoordinator,
        iface_config: dict,
        device_config: dict,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.iface_config = iface_config
        self.device_config = device_config
        self.iface_name = iface_config.get("name", "unknown")
        self.ssid = iface_config.get("ssid", "Unknown SSID")
        self.band = device_config.get("band", "Unknown")
        
        self._attr_name = f"WiFi {self.ssid} ({self.band})"
        self._attr_unique_id = f"{entry.entry_id}_wifi_{self.iface_name}"
        self._attr_icon = "mdi:wifi"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": MANUFACTURER,
            "model": coordinator.data.get("system_info", {}).get("model", "Unknown"),
            "sw_version": coordinator.data.get("system_info", {}).get("firmware_version", "Unknown"),
        }

    @property
    def is_on(self) -> bool:
        """Return true if the WiFi is enabled."""
        # Get the current state from coordinator data
        wifi_config = self.coordinator.data.get("wifi_config", {})
        for device in wifi_config.get("res", []):
            for iface in device.get("ifaces", []):
                if iface.get("name") == self.iface_name:
                    return iface.get("enabled", False)
        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        # Get current WiFi status
        wifi_status = self.coordinator.data.get("wifi_status_detail", {})
        device_status = None
        for device in wifi_status.get("res", []):
            if device.get("name") == self.device_config.get("device"):
                device_status = device
                break
        
        attrs = {
            "ssid": self.ssid,
            "band": self.band,
            "device": self.device_config.get("device"),
            "guest": self.iface_config.get("guest", False),
            "hidden": self.iface_config.get("hidden", False),
            "encryption": self.iface_config.get("encryption"),
            "channel": self.device_config.get("channel", 0),
            "htmode": self.device_config.get("htmode"),
            "hwmode": self.device_config.get("hwmode"),
            "txpower": self.device_config.get("txpower"),
        }
        
        if device_status:
            attrs["state"] = device_status.get("state", "unknown")
            attrs["current_channel"] = device_status.get("channel")
        
        return attrs

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the WiFi."""
        _LOGGER.debug("Enabling WiFi: %s", self.ssid)
        success = await self.coordinator.async_set_wifi_enabled(self.iface_name, True)
        if not success:
            _LOGGER.error("Failed to enable WiFi: %s", self.ssid)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the WiFi."""
        _LOGGER.debug("Disabling WiFi: %s", self.ssid)
        success = await self.coordinator.async_set_wifi_enabled(self.iface_name, False)
        if not success:
            _LOGGER.error("Failed to disable WiFi: %s", self.ssid)
