"""API client for GL.iNet routers."""
import hashlib
import json
import logging
import subprocess
from typing import Any, Dict, List, Optional

import requests

_LOGGER = logging.getLogger(__name__)


class GLiNetAPI:
    """API client for GL.iNet routers."""

    def __init__(self, host: str, username: str, password: str) -> None:
        """Initialize the API client."""
        self.host = host
        self.username = username
        self.password = password
        self.sid: Optional[str] = None
        self.session = requests.Session()
        self.session.timeout = 10

    def authenticate(self) -> bool:
        """Authenticate with the router."""
        try:
            # Get challenge
            challenge_data = {
                "jsonrpc": "2.0",
                "method": "challenge",
                "params": {"username": self.username},
                "id": 0
            }
            
            response = self.session.post(
                f"http://{self.host}/rpc",
                json=challenge_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            challenge_result = response.json()
            if "result" not in challenge_result:
                _LOGGER.error("No result in challenge response")
                return False
                
            result = challenge_result["result"]
            alg = result.get("alg")
            salt = result.get("salt")
            nonce = result.get("nonce")
            
            if not all([alg, salt, nonce]):
                _LOGGER.error("Missing challenge parameters")
                return False
            
            # Create cipher password using mkpasswd equivalent
            cipher_password = self._create_cipher_password(salt, self.password)
            
            # Create hash
            hash_string = f"{self.username}:{cipher_password}:{nonce}"
            hash_value = hashlib.md5(hash_string.encode()).hexdigest()
            
            # Login
            login_data = {
                "jsonrpc": "2.0",
                "method": "login",
                "params": {"username": self.username, "hash": hash_value},
                "id": 0
            }
            
            response = self.session.post(
                f"http://{self.host}/rpc",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            login_result = response.json()
            if "result" in login_result and "sid" in login_result["result"]:
                self.sid = login_result["result"]["sid"]
                _LOGGER.debug("Authentication successful")
                return True
            else:
                _LOGGER.error("Authentication failed: %s", login_result)
                return False
                
        except Exception as exc:
            _LOGGER.error("Authentication error: %s", exc)
            return False

    def _create_cipher_password(self, salt: str, password: str) -> str:
        """Create cipher password using MD5 crypt."""
        try:
            # Use subprocess to call mkpasswd if available
            result = subprocess.run(
                ["mkpasswd", "-m", "md5", "-S", salt, password],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to Python implementation
            return self._md5_crypt(password, salt)

    def _md5_crypt(self, password: str, salt: str) -> str:
        """Python implementation of MD5 crypt."""
        # This is a simplified version - for production use a proper crypt library
        magic = "$1$"
        if salt.startswith(magic):
            salt = salt[len(magic):]
        
        # Take only first 8 characters of salt
        salt = salt[:8]
        
        # Create the hash
        ctx = hashlib.md5()
        ctx.update(password.encode())
        ctx.update(magic.encode())
        ctx.update(salt.encode())
        
        ctx1 = hashlib.md5()
        ctx1.update(password.encode())
        ctx1.update(salt.encode())
        ctx1.update(password.encode())
        final = ctx1.digest()
        
        for i in range(len(password)):
            ctx.update(final[i % 16:i % 16 + 1])
            
        for i in range(len(password)):
            if i & 1:
                ctx.update(b'\0')
            else:
                ctx.update(password[0:1].encode())
                
        final = ctx.digest()
        
        # 1000 iterations
        for i in range(1000):
            ctx1 = hashlib.md5()
            if i & 1:
                ctx1.update(password.encode())
            else:
                ctx1.update(final)
                
            if i % 3:
                ctx1.update(salt.encode())
                
            if i % 7:
                ctx1.update(password.encode())
                
            if i & 1:
                ctx1.update(final)
            else:
                ctx1.update(password.encode())
                
            final = ctx1.digest()
        
        # Convert to base64-like encoding
        itoa64 = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        
        def to64(v, n):
            result = ""
            while n > 0:
                result += itoa64[v & 0x3f]
                v >>= 6
                n -= 1
            return result
        
        result = magic + salt + "$"
        result += to64((final[0] << 16) | (final[6] << 8) | final[12], 4)
        result += to64((final[1] << 16) | (final[7] << 8) | final[13], 4)
        result += to64((final[2] << 16) | (final[8] << 8) | final[14], 4)
        result += to64((final[3] << 16) | (final[9] << 8) | final[15], 4)
        result += to64((final[4] << 16) | (final[10] << 8) | final[5], 4)
        result += to64(final[11], 2)
        
        return result

    def _make_rpc_call(self, service: str, method: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make an RPC call to the router."""
        if not self.sid:
            if not self.authenticate():
                return None
                
        if params is None:
            params = {}
            
        data = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": [self.sid, service, method, params],
            "id": 1
        }
        
        try:
            response = self.session.post(
                f"http://{self.host}/rpc",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            if "result" in result:
                return result["result"]
            else:
                _LOGGER.error("No result in RPC response: %s", result)
                return None
                
        except Exception as exc:
            _LOGGER.error("RPC call error: %s", exc)
            return None

    def get_vpn_status(self, vpn_type: str) -> Optional[Dict]:
        """Get VPN status for a specific type."""
        return self._make_rpc_call(f"{vpn_type}-client", "get_status")

    def get_active_vpn(self) -> Optional[Dict]:
        """Get the currently active VPN."""
        for vpn_type in ["ovpn", "wg"]:
            status = self.get_vpn_status(vpn_type)
            if status and status.get("status") == 1:
                return status
        return {
            "status": 0,
            "group_id": None,
            "client_id": None,
            "peer_id": None,
            "rx_bytes": None,
            "tx_bytes": None,
            "name": None,
            "ipv4": None,
            "domain": None
        }

    def get_vpn_configs(self, vpn_type: str) -> List[Dict]:
        """Get all VPN configurations for a specific type."""
        result = self._make_rpc_call(f"{vpn_type}-client", "get_all_config_list")
        if not result or "config_list" not in result:
            return []
            
        configs = []
        for group in result["config_list"]:
            group_id = group.get("group_id")
            group_name = group.get("group_name")
            
            if vpn_type == "wg" and "peers" in group:
                for peer in group["peers"]:
                    configs.append({
                        "name": peer.get("name"),
                        "group_id": group_id,
                        "group_name": group_name,
                        "peer_id": peer.get("peer_id"),
                        "type": "wg"
                    })
            elif vpn_type == "ovpn" and "clients" in group:
                for client in group["clients"]:
                    configs.append({
                        "name": client.get("name"),
                        "group_id": group_id,
                        "group_name": group_name,
                        "client_id": client.get("client_id"),
                        "type": "ovpn"
                    })
                    
        return configs

    def get_all_vpn_configs(self) -> List[Dict]:
        """Get all VPN configurations."""
        configs = []
        configs.extend(self.get_vpn_configs("wg"))
        configs.extend(self.get_vpn_configs("ovpn"))
        return configs

    def start_vpn(self, vpn_config: Dict) -> bool:
        """Start a VPN connection."""
        vpn_type = vpn_config["type"]
        group_id = vpn_config["group_id"]
        
        if vpn_type == "wg":
            peer_id = vpn_config["peer_id"]
            params = {"group_id": group_id, "peer_id": peer_id}
        else:  # ovpn
            client_id = vpn_config["client_id"]
            params = {"group_id": group_id, "client_id": client_id}
            
        result = self._make_rpc_call(f"{vpn_type}-client", "start", params)
        return result is not None

    def stop_vpn(self, vpn_config: Dict) -> bool:
        """Stop a VPN connection."""
        vpn_type = vpn_config["type"]
        group_id = vpn_config["group_id"]
        
        if vpn_type == "wg":
            peer_id = vpn_config["peer_id"]
            params = {"group_id": group_id, "peer_id": peer_id}
        else:  # ovpn
            client_id = vpn_config["client_id"]
            params = {"group_id": group_id, "client_id": client_id}
            
        result = self._make_rpc_call(f"{vpn_type}-client", "stop", params)
        return result is not None

    def stop_all_vpns(self) -> bool:
        """Stop all active VPN connections."""
        success = True
        for vpn_type in ["ovpn", "wg"]:
            status = self.get_vpn_status(vpn_type)
            if status and status.get("status") == 1:
                group_id = status.get("group_id")
                if vpn_type == "wg":
                    peer_id = status.get("peer_id")
                    params = {"group_id": group_id, "peer_id": peer_id}
                else:
                    client_id = status.get("client_id")
                    params = {"group_id": group_id, "client_id": client_id}
                    
                result = self._make_rpc_call(f"{vpn_type}-client", "stop", params)
                if not result:
                    success = False
                    
        return success

    def get_system_status(self) -> Optional[Dict]:
        """Get system status."""
        return self._make_rpc_call("system", "get_status")

    def get_system_info(self) -> Optional[Dict]:
        """Get system information."""
        return self._make_rpc_call("system", "get_info")

    def get_disk_info(self) -> Optional[Dict]:
        """Get disk information."""
        return self._make_rpc_call("system", "disk_info")

    def reboot_system(self) -> bool:
        """Reboot the system."""
        result = self._make_rpc_call("system", "reboot")
        return result is not None

    def check_firmware_online(self) -> Optional[Dict]:
        """Check for firmware updates."""
        return self._make_rpc_call("system", "check_firmware_online")

    def get_timezone_config(self) -> Optional[Dict]:
        """Get timezone configuration."""
        return self._make_rpc_call("system", "get_timezone_config")

    def get_load(self) -> Optional[Dict]:
        """Get CPU load and memory information."""
        return self._make_rpc_call("system", "get_load")

    def get_unixtime(self) -> Optional[Dict]:
        """Get Unix timestamp."""
        return self._make_rpc_call("system", "get_unixtime")

    def get_httpd_mem_status(self) -> Optional[Dict]:
        """Get HTTP server memory usage."""
        return self._make_rpc_call("system", "get_httpd_mem_status")

    def get_security_policy(self) -> Optional[Dict]:
        """Get security policy settings."""
        return self._make_rpc_call("system", "get_security_policy")

    # Firewall methods
    def get_firewall_rules(self) -> Optional[Dict]:
        """Get firewall rule list."""
        return self._make_rpc_call("firewall", "get_rule_list")

    def add_firewall_rule(self, rule_params: Dict[str, Any]) -> Optional[Dict]:
        """Add a firewall rule."""
        return self._make_rpc_call("firewall", "add_rule", rule_params)

    def remove_firewall_rule(self, rule_id: str = None, remove_all: bool = False) -> Optional[Dict]:
        """Remove a firewall rule."""
        params = {}
        if remove_all:
            params["all"] = True
        elif rule_id:
            params["id"] = rule_id
        return self._make_rpc_call("firewall", "remove_rule", params)

    def set_firewall_rule(self, rule_id: str, rule_params: Dict[str, Any]) -> Optional[Dict]:
        """Modify an existing firewall rule."""
        params = rule_params.copy()
        params["id"] = rule_id
        return self._make_rpc_call("firewall", "set_rule", params)

    def get_dmz_config(self) -> Optional[Dict]:
        """Get DMZ configuration."""
        return self._make_rpc_call("firewall", "get_dmz")

    def set_dmz_config(self, enabled: bool, dest_ip: str = None) -> Optional[Dict]:
        """Set DMZ configuration."""
        params = {"enabled": enabled}
        if enabled and dest_ip:
            params["dest_ip"] = dest_ip
        return self._make_rpc_call("firewall", "set_dmz", params)

    def get_port_forward_list(self) -> Optional[Dict]:
        """Get port forward list."""
        return self._make_rpc_call("firewall", "get_port_forward_list")

    def add_port_forward(self, forward_params: Dict[str, Any]) -> Optional[Dict]:
        """Add port forward rule."""
        return self._make_rpc_call("firewall", "add_port_forward", forward_params)

    def set_port_forward(self, rule_id: str, forward_params: Dict[str, Any]) -> Optional[Dict]:
        """Modify an existing port forward rule."""
        params = forward_params.copy()
        params["id"] = rule_id
        return self._make_rpc_call("firewall", "set_port_forward", params)

    def remove_port_forward(self, rule_id: str = None, remove_all: bool = False) -> Optional[Dict]:
        """Remove port forward rule."""
        params = {}
        if remove_all:
            params["all"] = True
        elif rule_id:
            params["id"] = rule_id
        return self._make_rpc_call("firewall", "remove_port_forward", params)

    def get_wan_access(self) -> Optional[Dict]:
        """Get WAN access configuration."""
        return self._make_rpc_call("firewall", "get_wan_access")

    def set_wan_access(self, config: Dict[str, Any]) -> Optional[Dict]:
        """Set WAN access configuration."""
        return self._make_rpc_call("firewall", "set_wan_access", config)

    def get_zone_list(self) -> Optional[Dict]:
        """Get firewall zone list."""
        return self._make_rpc_call("firewall", "get_zone_list")

    # WireGuard Server methods
    def get_wg_server_status(self) -> Optional[Dict]:
        """Get WireGuard server status."""
        return self._make_rpc_call("wg-server", "get_status")

    def start_wg_server(self) -> Optional[Dict]:
        """Start WireGuard server."""
        return self._make_rpc_call("wg-server", "start")

    def stop_wg_server(self) -> Optional[Dict]:
        """Stop WireGuard server."""
        return self._make_rpc_call("wg-server", "stop")

    def get_wg_server_config(self) -> Optional[Dict]:
        """Get WireGuard server configuration."""
        return self._make_rpc_call("wg-server", "get_config")

    def set_wg_server_config(self, config: Dict[str, Any]) -> Optional[Dict]:
        """Set WireGuard server configuration."""
        return self._make_rpc_call("wg-server", "set_config", config)

    def set_wg_server_peer(self, peer_config: Dict[str, Any]) -> Optional[Dict]:
        """Modify WireGuard peer configuration."""
        return self._make_rpc_call("wg-server", "set_peer", peer_config)

    # OpenVPN Server methods
    def get_ovpn_server_status(self) -> Optional[Dict]:
        """Get OpenVPN server status."""
        return self._make_rpc_call("ovpn-server", "get_status")

    def start_ovpn_server(self) -> Optional[Dict]:
        """Start OpenVPN server."""
        return self._make_rpc_call("ovpn-server", "start")

    def stop_ovpn_server(self) -> Optional[Dict]:
        """Stop OpenVPN server."""
        return self._make_rpc_call("ovpn-server", "stop")

    def get_clients(self) -> List[Dict]:
        """Get all connected clients."""
        result = self._make_rpc_call("clients", "get_list")
        if not result or "clients" not in result:
            return []
        return result.get("clients", [])

    # WiFi methods
    def get_wifi_config(self) -> Optional[Dict]:
        """Get WiFi configuration."""
        return self._make_rpc_call("wifi", "get_config")

    def set_wifi_config(self, config: Dict[str, Any]) -> Optional[Dict]:
        """Set WiFi configuration."""
        return self._make_rpc_call("wifi", "set_config", config)

    def get_wifi_status(self) -> Optional[Dict]:
        """Get WiFi device status."""
        return self._make_rpc_call("wifi", "get_status")
