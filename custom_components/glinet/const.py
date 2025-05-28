"""Constants for the GL.iNet integration."""

DOMAIN = "glinet"
MANUFACTURER = "GL.iNet"

# Configuration keys
CONF_HOST = "host"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

# Default values
DEFAULT_HOST = "192.168.8.1"
DEFAULT_USERNAME = "root"
DEFAULT_SCAN_INTERVAL = 30

# API endpoints
API_ENDPOINT = "/rpc"

# VPN types
VPN_TYPE_WIREGUARD = "wg"
VPN_TYPE_OPENVPN = "ovpn"

# Sensor types
SENSOR_VPN_STATUS = "vpn_status"
SENSOR_SYSTEM_STATUS = "system_status"
SENSOR_SYSTEM_INFO = "system_info"
SENSOR_DISK_INFO = "disk_info"

# Switch types
SWITCH_VPN = "vpn"

# Button types
BUTTON_REBOOT = "reboot"
BUTTON_CHECK_FIRMWARE = "check_firmware"
