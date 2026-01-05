// WiFi Configuration File
// Copy this file to src/wifi_config.h and update with your credentials
// Or update the credentials directly in src/main.cpp

#ifndef WIFI_CONFIG_H
#define WIFI_CONFIG_H

// WiFi Network Credentials
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// Dashboard Server Configuration
// Replace with your computer's IP address where the Flask server is running
// Find your IP: 
//   Windows: ipconfig (look for IPv4 Address)
//   Linux/Mac: ifconfig or ip addr
#define SERVER_URL "http://192.168.1.100:5000/api/data"

#endif

