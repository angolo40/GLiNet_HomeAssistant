"""Button platform for GL.iNet integration."""
import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
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
    """Set up GL.iNet buttons."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        GLiNetRebootButton(coordinator, entry),
        GLiNetStopAllVPNsButton(coordinator, entry),
        GLiNetCheckFirmwareButton(coordinator, entry),
    ]
    
    async_add_entities(entities)


class GLiNetButton(CoordinatorEntity, ButtonEntity):
    """Base class for GL.iNet buttons."""

    def __init__(
        self,
        coordinator: GLiNetDataUpdateCoordinator,
        entry: ConfigEntry,
        name: str,
        icon: str,
        unique_id_suffix: str,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{unique_id_suffix}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": MANUFACTURER,
            "model": coordinator.data.get("system_info", {}).get("model", "Unknown"),
            "sw_version": coordinator.data.get("system_info", {}).get("firmware_version", "Unknown"),
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success


class GLiNetRebootButton(GLiNetButton):
    """Button to reboot the router."""

    def __init__(
        self,
        coordinator: GLiNetDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the reboot button."""
        super().__init__(
            coordinator,
            entry,
            "Reboot Router",
            "mdi:restart",
            "reboot"
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Rebooting GL.iNet router")
        success = await self.coordinator.async_reboot_system()
        if success:
            _LOGGER.info("Reboot command sent successfully")
        else:
            _LOGGER.error("Failed to send reboot command")


class GLiNetStopAllVPNsButton(GLiNetButton):
    """Button to stop all VPN connections."""

    def __init__(
        self,
        coordinator: GLiNetDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the stop all VPNs button."""
        super().__init__(
            coordinator,
            entry,
            "Stop All VPNs",
            "mdi:vpn-outline",
            "stop_all_vpns"
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Stopping all VPN connections")
        success = await self.coordinator.async_stop_all_vpns()
        if success:
            _LOGGER.info("All VPN connections stopped successfully")
        else:
            _LOGGER.error("Failed to stop VPN connections")


class GLiNetCheckFirmwareButton(GLiNetButton):
    """Button to check for firmware updates."""

    def __init__(
        self,
        coordinator: GLiNetDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the check firmware button."""
        super().__init__(
            coordinator,
            entry,
            "Check Firmware",
            "mdi:update",
            "check_firmware"
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Checking for firmware updates")
        result = await self.coordinator.async_check_firmware()
        if result:
            _LOGGER.info("Firmware check completed: %s", result)
        else:
            _LOGGER.error("Failed to check firmware updates")
