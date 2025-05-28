"""Sensor platform for GL.iNet integration."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorEntity, 
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfInformation,
    UnitOfTemperature,
    UnitOfTime
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import GLiNetDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTIONS = [
    # VPN Status
    SensorEntityDescription(
        key="vpn_status",
        name="VPN Status",
        icon="mdi:vpn",
    ),
    
    # System Status Sensors
    SensorEntityDescription(
        key="system_uptime",
        name="System Uptime",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.TOTAL,
    ),
    SensorEntityDescription(
        key="cpu_load_1min",
        name="CPU Load (1 min)",
        icon="mdi:cpu-64-bit",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="cpu_load_5min",
        name="CPU Load (5 min)",
        icon="mdi:cpu-64-bit",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="cpu_load_15min",
        name="CPU Load (15 min)",
        icon="mdi:cpu-64-bit",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="cpu_temperature",
        name="CPU Temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="memory_usage",
        name="Memory Usage",
        icon="mdi:memory",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="memory_free",
        name="Memory Free",
        icon="mdi:memory",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="memory_total",
        name="Memory Total",
        icon="mdi:memory",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="flash_usage",
        name="Flash Storage Usage",
        icon="mdi:harddisk",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="flash_free",
        name="Flash Storage Free",
        icon="mdi:harddisk",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="flash_total",
        name="Flash Storage Total",
        icon="mdi:harddisk",
        device_class=SensorDeviceClass.DATA_SIZE,
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="battery_level",
        name="Battery Level",
        icon="mdi:battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="battery_temperature",
        name="Battery Temperature",
        icon="mdi:battery-thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="battery_charging",
        name="Battery Charging Status",
        icon="mdi:battery-charging",
    ),
    SensorEntityDescription(
        key="battery_cycles",
        name="Battery Charge Cycles",
        icon="mdi:battery-sync",
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="wifi_clients",
        name="WiFi Clients",
        icon="mdi:wifi",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="wired_clients",
        name="Wired Clients",
        icon="mdi:ethernet",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="total_clients",
        name="Total Clients",
        icon="mdi:devices",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="wan_status",
        name="WAN Status",
        icon="mdi:wan",
    ),
    SensorEntityDescription(
        key="system_mode",
        name="System Mode",
        icon="mdi:router-wireless-settings",
    ),
    
    # Network Interface Status
    SensorEntityDescription(
        key="network_interfaces",
        name="Network Interfaces",
        icon="mdi:network",
    ),
    
    # WiFi Status
    SensorEntityDescription(
        key="wifi_status",
        name="WiFi Status",
        icon="mdi:wifi-settings",
    ),
    
    # Services Status
    SensorEntityDescription(
        key="services_status",
        name="Services Status",
        icon="mdi:cog",
    ),
    
    # System Info
    SensorEntityDescription(
        key="system_info",
        name="System Info",
        icon="mdi:information",
    ),
    
    # Disk Info
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
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        system_status = self.coordinator.data.get("system_status", {})
        system_info = self.coordinator.data.get("system_info", {})
        disk_info = self.coordinator.data.get("disk_info", {})
        vpn_status = self.coordinator.data.get("vpn_status", {})
        
        key = self.entity_description.key
        
        # VPN Status
        if key == "vpn_status":
            if vpn_status.get("status") == 1:
                return "Connected"
            return "Disconnected"
        
        # System Status derived sensors
        elif key == "system_uptime":
            return system_status.get("system", {}).get("uptime")
        
        elif key == "cpu_load_1min":
            load_avg = system_status.get("system", {}).get("load_average", [])
            return load_avg[0] if len(load_avg) > 0 else None
        
        elif key == "cpu_load_5min":
            load_avg = system_status.get("system", {}).get("load_average", [])
            return load_avg[1] if len(load_avg) > 1 else None
        
        elif key == "cpu_load_15min":
            load_avg = system_status.get("system", {}).get("load_average", [])
            return load_avg[2] if len(load_avg) > 2 else None
        
        elif key == "cpu_temperature":
            return system_status.get("system", {}).get("cpu", {}).get("temperature")
        
        elif key == "memory_usage":
            system_data = system_status.get("system", {})
            total = system_data.get("memory_total", 0)
            free = system_data.get("memory_free", 0)
            if total > 0:
                return round(((total - free) / total) * 100, 1)
            return None
        
        elif key == "memory_free":
            memory_free = system_status.get("system", {}).get("memory_free", 0)
            return round(memory_free / (1024 * 1024), 1) if memory_free else None
        
        elif key == "memory_total":
            memory_total = system_status.get("system", {}).get("memory_total", 0)
            return round(memory_total / (1024 * 1024), 1) if memory_total else None
        
        elif key == "flash_usage":
            system_data = system_status.get("system", {})
            total = system_data.get("flash_total", 0)
            free = system_data.get("flash_free", 0)
            if total > 0:
                return round(((total - free) / total) * 100, 1)
            return None
        
        elif key == "flash_free":
            flash_free = system_status.get("system", {}).get("flash_free", 0)
            return round(flash_free / (1024 * 1024), 1) if flash_free else None
        
        elif key == "flash_total":
            flash_total = system_status.get("system", {}).get("flash_total", 0)
            return round(flash_total / (1024 * 1024), 1) if flash_total else None
        
        elif key == "battery_level":
            return system_status.get("system", {}).get("mcu", {}).get("charge_percent")
        
        elif key == "battery_temperature":
            return system_status.get("system", {}).get("mcu", {}).get("temperature")
        
        elif key == "battery_charging":
            charging_status = system_status.get("system", {}).get("mcu", {}).get("charging_status")
            if charging_status == 1:
                return "Charging"
            elif charging_status == 0:
                return "Not Charging"
            return "Unknown"
        
        elif key == "battery_cycles":
            return system_status.get("system", {}).get("mcu", {}).get("charge_cnt")
        
        elif key == "wifi_clients":
            clients = system_status.get("client", [])
            return clients[0].get("wireless_total", 0) if clients else 0
        
        elif key == "wired_clients":
            clients = system_status.get("client", [])
            return clients[0].get("cable_total", 0) if clients else 0
        
        elif key == "total_clients":
            clients = system_status.get("client", [])
            if clients:
                wireless = clients[0].get("wireless_total", 0)
                wired = clients[0].get("cable_total", 0)
                return wireless + wired
            return 0
        
        elif key == "wan_status":
            network = system_status.get("network", [])
            wan_interface = next((iface for iface in network if iface.get("interface") == "wan"), None)
            if wan_interface:
                if wan_interface.get("online"):
                    return "Online"
                elif wan_interface.get("up"):
                    return "Up (No Internet)"
                else:
                    return "Down"
            return "Unknown"
        
        elif key == "system_mode":
            mode = system_status.get("system", {}).get("mode", 0)
            mode_map = {
                0: "Router",
                1: "WDS",
                2: "Relay/Extender",
                3: "Mesh",
                4: "Access Point",
                5: "Unknown",
                6: "Passthrough"
            }
            return mode_map.get(mode, "Unknown")
        
        elif key == "network_interfaces":
            network = system_status.get("network", [])
            online_count = sum(1 for iface in network if iface.get("online"))
            return f"{online_count}/{len(network)} Online"
        
        elif key == "wifi_status":
            wifi = system_status.get("wifi", [])
            active_count = sum(1 for w in wifi if w.get("up"))
            return f"{active_count}/{len(wifi)} Active"
        
        elif key == "services_status":
            services = system_status.get("service", [])
            running_count = sum(1 for svc in services if svc.get("status") == 1)
            return f"{running_count}/{len(services)} Running"
        
        elif key == "system_info":
            return "Available" if system_info else "Unavailable"
        
        elif key == "disk_info":
            return "Available" if disk_info else "Unavailable"
        
        return "Unknown"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        system_status = self.coordinator.data.get("system_status", {})
        system_info = self.coordinator.data.get("system_info", {})
        disk_info = self.coordinator.data.get("disk_info", {})
        vpn_status = self.coordinator.data.get("vpn_status", {})
        
        key = self.entity_description.key
        
        if key == "vpn_status":
            return {
                "name": vpn_status.get("name"),
                "ipv4": vpn_status.get("ipv4"),
                "domain": vpn_status.get("domain"),
                "rx_bytes": vpn_status.get("rx_bytes"),
                "tx_bytes": vpn_status.get("tx_bytes"),
                "group_id": vpn_status.get("group_id"),
                "client_id": vpn_status.get("client_id"),
                "peer_id": vpn_status.get("peer_id"),
            }
        
        elif key == "network_interfaces":
            network = system_status.get("network", [])
            interfaces = {}
            for iface in network:
                name = iface.get("interface", "unknown")
                interfaces[name] = {
                    "up": iface.get("up", False),
                    "online": iface.get("online", False)
                }
            return interfaces
        
        elif key == "wifi_status":
            wifi = system_status.get("wifi", [])
            wifi_info = {}
            for w in wifi:
                name = w.get("name", "unknown")
                wifi_info[name] = {
                    "ssid": w.get("ssid"),
                    "up": w.get("up", False),
                    "band": w.get("band"),
                    "channel": w.get("channel"),
                    "guest": w.get("guest", False),
                    "password": w.get("passwd", "***") if w.get("passwd") else None
                }
            return wifi_info
        
        elif key == "services_status":
            services = system_status.get("service", [])
            service_info = {}
            for svc in services:
                name = svc.get("name", "unknown")
                status = svc.get("status", 0)
                status_text = {0: "Disabled", 1: "Running", 2: "Connecting"}.get(status, "Unknown")
                service_info[name] = {
                    "status": status_text,
                    "group_id": svc.get("group_id"),
                    "client_id": svc.get("client_id"),
                    "peer_id": svc.get("peer_id")
                }
            return service_info
        
        elif key == "system_info":
            return {
                "mac": system_info.get("mac"),
                "model": system_info.get("model"),
                "firmware_version": system_info.get("firmware_version"),
                "firmware_date": system_info.get("firmware_date"),
                "firmware_type": system_info.get("firmware_type"),
                "hardware_version": system_info.get("hardware_version"),
                "vendor": system_info.get("vendor"),
                "sn": system_info.get("sn"),
                "cpu_num": system_info.get("cpu_num"),
                "country_code": system_info.get("country_code"),
                "architecture": system_info.get("board_info", {}).get("architecture"),
                "kernel_version": system_info.get("board_info", {}).get("kernel_version"),
                "openwrt_version": system_info.get("board_info", {}).get("openwrt_version"),
            }
        
        elif key == "disk_info":
            return {
                "root": disk_info.get("root", {}),
                "tmp": disk_info.get("tmp", {}),
            }
        
        elif key in ["memory_usage", "memory_free", "memory_total"]:
            system_data = system_status.get("system", {})
            return {
                "memory_total_bytes": system_data.get("memory_total"),
                "memory_free_bytes": system_data.get("memory_free"),
                "memory_buff_cache_bytes": system_data.get("memory_buff_cache"),
            }
        
        elif key in ["flash_usage", "flash_free", "flash_total"]:
            system_data = system_status.get("system", {})
            return {
                "flash_total_bytes": system_data.get("flash_total"),
                "flash_free_bytes": system_data.get("flash_free"),
                "flash_app_bytes": system_data.get("flash_app"),
            }
        
        elif key in ["battery_level", "battery_temperature", "battery_charging", "battery_cycles"]:
            mcu_data = system_status.get("system", {}).get("mcu", {})
            return {
                "charge_percent": mcu_data.get("charge_percent"),
                "temperature": mcu_data.get("temperature"),
                "charging_status": mcu_data.get("charging_status"),
                "charge_cycles": mcu_data.get("charge_cnt"),
            }
        
        elif key == "system_mode":
            system_data = system_status.get("system", {})
            return {
                "lan_ip": system_data.get("lan_ip"),
                "lan_netmask": system_data.get("lan_netmask"),
                "guest_ip": system_data.get("guest_ip"),
                "guest_netmask": system_data.get("guest_netmask"),
                "ipv6_enabled": system_data.get("ipv6_enabled"),
                "ddns_enabled": system_data.get("ddns_enabled"),
                "netnat_enabled": system_data.get("netnat_enabled"),
                "timestamp": system_data.get("timestamp"),
            }
        
        return {}

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
