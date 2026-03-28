# TCL AC IR Blaster

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-GPLv3-green.svg)

Home Assistant integration for controlling **TCL Air Conditioners** using Infrared (IR) commands sent via **Zigbee2MQTT**.

## 🚀 Features

- Full Climate entity support (HVAC modes, Fan speed, Presets).
- Real-time state synchronization via MQTT.
- Support for external temperature sensors for precise climate control.
- Compatible with generic Tuya IR Blasters.

## 📋 Requirements

- **Zigbee2MQTT**: Modern version with an IR Blaster already paired and functional.
- **IR Blaster**: Tested and confirmed working with model **UFO-R11**. It should work with most **Tuya-based** IR blasters supported by Z2M that accept base64 encoded IR commands.

## 🛠️ Installation

### Via HACS (Recommended)

1. Open **HACS** in Home Assistant.
2. Go to **Integrations** and click the three dots in the top right corner.
3. Select **Custom repositories**.
4. Add `https://github.com/danielcurly/TCL-AC-IR-Blaster` with category **Integration**.
5. Click **Add** and then **Install** the newly appeared integration.
6. Restart Home Assistant.

### Manual Installation

1. Copy the `custom_components/tcl_ac` folder into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## ⚙️ Configuration

The integration is configured via the Home Assistant UI (**Settings > Devices & Services > Add Integration > TCL AC IR Blaster**).

### Parameters:

- **MQTT IR Entity Name**: The exact name of the entity in Zigbee2MQTT (e.g., `salón_ir_blaster`).
- **Temperature Sensor (Optional)**: The **full entity ID** of your temperature sensor (e.g., `sensor.temperatura_salon_temperature`).

## ⚖️ License

This project is licensed under the **GPLv3 License**.

---
*Developed by danielcurly*
