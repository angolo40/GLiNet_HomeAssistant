# GLiNet Home Assistant Integration

[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg?cacheSeconds=2592000)](https://github.com/angolo40/GLiNet_HomeAssistant)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A custom Home Assistant integration for managing GL.iNet routers, providing comprehensive control over VPN connections, system monitoring, and router management directly from your Home Assistant dashboard.

## 🚀 Features

- **VPN Management**: Start, stop, and monitor VPN connections (WireGuard and OpenVPN)
- **System Monitoring**: Real-time system status, disk usage, and network information
- **Router Control**: Reboot router, check firmware updates, and manage settings
- **Multiple Entities**: Sensors, switches, and buttons for complete router control

## 📋 Supported Devices

This integration is designed for GL.iNet routers running firmware 4.x. It has been tested on:

- **Model**: GL-MT300N-V2
- **Firmware**: 4.3.11

Other GL.iNet router models with 4.x firmware should also work, but may require testing.

## 🛠️ Installation

### HACS Installation (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/angolo40/GLiNet_HomeAssistant`
6. Select "Integration" as the category
7. Click "Add"
8. Search for "GLiNet" and install

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/angolo40/GLiNet_HomeAssistant/releases)
2. Extract the `custom_components/glinet` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## ⚙️ Configuration

### Adding the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "GLiNet"
4. Enter your router's configuration:
   - **Host**: Your router's IP address (e.g., `192.168.8.1`)
   - **Username**: Router username (usually `root`)
   - **Password**: Router password

## 🔧 API Reference

This integration uses the GL.iNet 4.x API. The API documentation was retrieved from the Wayback Machine as the original documentation is no longer available online:
[GL.iNet 4.x API Documentation](https://web.archive.org/web/20240106020516/https://dev.gl-inet.com/router-4.x-api/)


## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.


## 👤 Author

**Giuseppe Trifilio**

- GitHub: [@angolo40](https://github.com/angolo40)
- Project Link: [https://github.com/angolo40/GLiNet_HomeAssistant](https://github.com/angolo40/GLiNet_HomeAssistant)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🌟 Support

If this integration helped you, please consider giving it a ⭐️ on GitHub!

For support, please open an issue on the [GitHub repository](https://github.com/angolo40/GLiNet_HomeAssistant/issues).

---

**Note**: This integration is not officially affiliated with GL.iNet. It's a community-developed integration for Home Assistant users.
