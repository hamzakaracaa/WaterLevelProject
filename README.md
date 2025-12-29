# Water Level Monitoring System

A professional water level monitoring system for ESP32 with a modern Python GUI application. This project was developed for Haier Europe R&D as a Smart Dryer Monitor solution.

![Version](https://img.shields.io/badge/version-2.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-ESP32-orange.svg)
![Python](https://img.shields.io/badge/python-3.7+-green.svg)

## 📋 Table of Contents

- [Features](#features)
- [Hardware Requirements](#hardware-requirements)
- [Software Requirements](#software-requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

- **Real-time Water Level Monitoring**: Continuous monitoring of water tank levels via ESP32
- **Modern GUI Interface**: Beautiful, responsive Tkinter-based graphical user interface
- **Data Filtering**: Moving average filter to reduce sensor noise and provide stable readings
- **Calibration System**: Easy-to-use calibration buttons for setting min/max water levels
- **Data Logging**: CSV export functionality for data analysis and record keeping
- **Visual Feedback**: Animated water tank visualization with color-coded status indicators
- **Error Handling**: Robust error handling for serial communication and file operations

## 🔧 Hardware Requirements

- **ESP32 Development Board** (ESP32-DOIT-DevKit-V1)
- **Water Level Sensor** (Analog capacitive sensor)
- **Connections**:
  - Sensor Power (Red wire) → GPIO 32
  - Sensor Data (Yellow/Orange wire) → GPIO 34 (ADC1_CH6)
  - Sensor GND → GND

### Wiring Diagram

```
ESP32                    Water Level Sensor
------                   ------------------
GPIO 32  ──────────────> Power (Red)
GPIO 34  ──────────────> Data (Yellow/Orange)
GND      ──────────────> GND
```

## 💻 Software Requirements

- **PlatformIO** (for ESP32 firmware)
- **Python 3.7+**
- **Python Dependencies**:
  - `pyserial >= 3.5`
  - `tkinter` (usually included with Python)

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/hamzakaracaa/WaterLevelProject.git
cd WaterLevelProject
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Upload Firmware to ESP32

Using PlatformIO:

```bash
# Connect ESP32 to your computer
# Update COM port in platformio.ini if needed (default: COM3)

# Build and upload
pio run --target upload

# Monitor serial output
pio device monitor
```

Or use PlatformIO IDE:
1. Open the project in PlatformIO
2. Click "Upload" button
3. Verify connection in Serial Monitor

### 4. Configure Serial Port (if needed)

Edit `src/main.py` and update the serial port:

```python
SERIAL_PORT = 'COM3'  # Change to your port (e.g., 'COM4', '/dev/ttyUSB0', '/dev/cu.usbserial-*')
BAUD_RATE = 115200
```

**Finding your serial port:**
- **Windows**: Device Manager → Ports (COM & LPT)
- **Linux/Mac**: `ls /dev/tty*` or `ls /dev/cu*`

## 🚀 Usage

### Starting the Application

```bash
python src/main.py
```

### Using the Interface

1. **Connection**: The application will automatically attempt to connect to the ESP32. Status is shown at the top.

2. **Calibration**:
   - **Set Min Level**: Click when the tank is empty to set the minimum value
   - **Set Max Level**: Click when the tank is full to set the maximum value

3. **Data Logging**:
   - Check "📊 Save Data (.csv)" to enable logging
   - CSV files are saved in the project root directory
   - Format: `sensor_log_YYYYMMDD_HHMMSS.csv`

4. **Monitoring**:
   - Real-time water level percentage is displayed
   - Color coding:
     - 🔴 Red: < 10% (Low)
     - 🔵 Blue: 10-90% (Normal)
     - 🟡 Yellow: > 90% (High)

## 📁 Project Structure

```
WaterLevelProject/
├── src/
│   ├── main.cpp          # ESP32 firmware (Arduino)
│   └── main.py           # Python GUI application
├── platformio.ini        # PlatformIO configuration
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── .gitignore           # Git ignore rules
└── water_icon.ico       # Application icon
```

## ⚙️ Configuration

### ESP32 Configuration

Edit `platformio.ini` to change:
- Board type
- Serial port
- Upload speed

### Python Application Configuration

Edit `src/main.py`:
- `SERIAL_PORT`: Serial port name
- `BAUD_RATE`: Communication speed (default: 115200)
- `calib_min`/`calib_max`: Default calibration values
- `data_buffer.maxlen`: Filter buffer size (default: 20)

## 🔍 Troubleshooting

### Connection Issues

**Problem**: "No Connection!" message
- **Solution**: 
  - Verify ESP32 is connected and powered
  - Check COM port in `main.py` matches your system
  - Ensure no other program is using the serial port
  - Try unplugging and reconnecting the ESP32

### Incorrect Readings

**Problem**: Water level percentage seems wrong
- **Solution**: 
  - Recalibrate using "Set Min Level" and "Set Max Level" buttons
  - Check sensor connections
  - Verify sensor is properly submerged/positioned

### CSV Logging Not Working

**Problem**: CSV files not being created
- **Solution**:
  - Check file permissions in project directory
  - Ensure sufficient disk space
  - Verify checkbox is enabled

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'serial'`
- **Solution**: 
  ```bash
  pip install -r requirements.txt
  ```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Hamza Karaca - Haier Europe R&D Team Intern**

## 🙏 Acknowledgments

- Built with [PlatformIO](https://platformio.org/)
- GUI created with [Tkinter](https://docs.python.org/3/library/tkinter.html)
- Serial communication via [PySerial](https://pyserial.readthedocs.io/)

---

**Note**: This project is designed for ESP32-DOIT-DevKit-V1. For other ESP32 boards, you may need to adjust pin configurations in `main.cpp`.

