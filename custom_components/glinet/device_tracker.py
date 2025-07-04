"""Support for GL.iNet routers as device trackers."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.components.device_tracker.const import SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GLiNetDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up device tracker for GL.iNet component."""
    coordinator: GLiNetDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    tracked_devices = {}

    @callback
    def update_devices():
        """Update the values of the devices."""
        if not coordinator.data or "clients" not in coordinator.data:
            _LOGGER.debug("No client data in coordinator update")
            return
            
        new_devices = []
        client_list = coordinator.data["clients"]

        for client_data in client_list:
            if not client_data.get("mac"):
                continue

            mac_address = client_data["mac"].upper()
            if mac_address in tracked_devices:
                tracked_devices[mac_address].client_data = client_data
                tracked_devices[mac_address].async_write_ha_state()
            else:
                new_device = GlinetScannerEntity(coordinator, client_data)
                tracked_devices[mac_address] = new_device
                new_devices.append(new_device)
        
        if new_devices:
            async_add_entities(new_devices)

    entry.async_on_unload(coordinator.async_add_listener(update_devices))
    update_devices()


class GlinetScannerEntity(CoordinatorEntity[GLiNetDataUpdateCoordinator], ScannerEntity):
    """A GL.iNet client tracker."""

    def __init__(
        self,
        coordinator: GLiNetDataUpdateCoordinator,
        client_data: dict[str, Any],
    ) -> None:
        """Initialize a GL.iNet tracker entity."""
        super().__init__(coordinator)
        self.client_data = client_data

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self.client_data["mac"].upper()

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self.client_data.get("name") or self.ip_address or self.unique_id

    @property
    def is_connected(self) -> bool:
        """Return true if the device is connected to the network."""
        mac = self.unique_id
        for client in self.coordinator.data.get("clients", []):
            if client.get("mac", "").upper() == mac:
                return client.get("online", False)
        return False

    @property
    def source_type(self) -> str:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.ROUTER

    @property
    def ip_address(self) -> str | None:
        """Return the primary ip address of the device."""
        return self.client_data.get("ip")

    @property
    def mac_address(self) -> str:
        """Return the mac address of the device."""
        return self.unique_id

    @property
    def hostname(self) -> str | None:
        """Return hostname of the device."""
        return self.client_data.get("name")

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information."""
        return DeviceInfo(
            connections={("mac", self.mac_address)},
            default_name=self.name,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = {}
        if self.client_data.get("iface"):
            attrs["iface"] = self.client_data["iface"]
        if self.client_data.get("remote"):
            attrs["remote"] = self.client_data["remote"]
        if self.client_data.get("vendor"):
            attrs["vendor"] = self.client_data["vendor"]
        
        return attrs 
