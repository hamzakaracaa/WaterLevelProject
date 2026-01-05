# WiFi Setup Guide

This guide will help you configure the ESP32 to send data wirelessly to the dashboard.

## Step 1: Configure WiFi Credentials

You have two options:

### Option A: Edit directly in `src/main.cpp`
1. Open `src/main.cpp`
2. Find these lines:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
3. Replace with your WiFi network name and password

### Option B: Use configuration file (recommended)
1. Copy `wifi_config.h` to `src/wifi_config.h`
2. Update the credentials in `src/wifi_config.h`
3. Add `#include "wifi_config.h"` at the top of `src/main.cpp`
4. Replace the hardcoded values with:
   ```cpp
   const char* ssid = WIFI_SSID;
   const char* password = WIFI_PASSWORD;
   const char* serverURL = SERVER_URL;
   ```

## Step 2: Find Your Computer's IP Address

The ESP32 needs to know where to send the data. Find your computer's IP address:

### Windows:
1. Open Command Prompt
2. Type: `ipconfig`
3. Look for "IPv4 Address" under your active network adapter
4. Example: `192.168.1.100`

### Linux/Mac:
1. Open Terminal
2. Type: `ifconfig` or `ip addr`
3. Look for your network interface (usually `wlan0` or `eth0`)
4. Find the `inet` address
5. Example: `192.168.1.100`

## Step 3: Update Server URL in ESP32 Code

1. Open `src/main.cpp`
2. Find this line:
   ```cpp
   const char* serverURL = "http://192.168.1.100:5000/api/data";
   ```
3. Replace `192.168.1.100` with your computer's IP address

**Important:** Make sure your computer and ESP32 are on the same WiFi network!

## Step 4: Start the Dashboard Server

1. Install Python dependencies (if not already done):
   ```bash
   pip install -r requirements.txt
   ```

2. Start the Flask server:
   ```bash
   python src/dashboard_server.py
   ```

3. You should see:
   ```
   ==================================================
   Water Level Dashboard Server
   ==================================================
   Dashboard URL: http://localhost:5000
   API Endpoint: http://localhost:5000/api/data
   ```

4. Open your web browser and go to:
   - `http://localhost:5000` (on your computer)
   - `http://YOUR_IP:5000` (from other devices on the same network)

## Step 5: Upload Firmware to ESP32

1. Make sure PlatformIO is installed
2. Upload the firmware:
   ```bash
   pio run --target upload
   ```

3. Open Serial Monitor to see connection status:
   ```bash
   pio device monitor
   ```

4. You should see:
   ```
   Connecting to WiFi: YOUR_WIFI_SSID
   ....
   WiFi connected!
   IP address: 192.168.1.XXX
   Data sent successfully. Response code: 200
   ```

## Troubleshooting

### ESP32 won't connect to WiFi
- Double-check SSID and password (case-sensitive!)
- Make sure your WiFi is 2.4GHz (ESP32 doesn't support 5GHz)
- Check Serial Monitor for error messages

### Dashboard not receiving data
- Verify your computer's IP address is correct
- Make sure the Flask server is running
- Check that both devices are on the same network
- Check Windows Firewall - it may be blocking port 5000
- Try accessing `http://YOUR_IP:5000/api/latest` in a browser to test

### Can't access dashboard from other devices
- Make sure Flask is running with `host='0.0.0.0'` (already configured)
- Check firewall settings on your computer
- Try accessing from the same device first: `http://localhost:5000`

### Port 5000 already in use
- Change the port in `dashboard_server.py`:
  ```python
  app.run(host='0.0.0.0', port=5001, debug=True)  # Use different port
  ```
- Update the `serverURL` in ESP32 code accordingly

## Testing the Connection

1. **Test ESP32 WiFi Connection:**
   - Check Serial Monitor for "WiFi connected!" message
   - Note the ESP32's IP address

2. **Test Dashboard Server:**
   - Open browser: `http://localhost:5000`
   - You should see the dashboard interface

3. **Test Data Transmission:**
   - Watch Serial Monitor for "Data sent successfully" messages
   - Check dashboard - it should update automatically

## Security Notes

⚠️ **Important:** The current setup is for local network use only. For production:
- Use HTTPS instead of HTTP
- Add authentication to the API
- Use environment variables for sensitive credentials
- Consider using a proper database instead of in-memory storage

