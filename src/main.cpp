#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>

// Water level sensor - PlatformIO code with WiFi capability
// Hardware hack: Use D32 pin as power source instead of 3.3V pin

#define SENSOR_POWER_PIN  32  // Power pin (red wire)
#define SENSOR_DATA_PIN   34  // Data pin (yellow/orange wire)

// WiFi credentials - UPDATE THESE WITH YOUR NETWORK INFO
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Dashboard server URL - UPDATE WITH YOUR COMPUTER'S IP ADDRESS
// Find your IP: Windows: ipconfig, Linux/Mac: ifconfig
const char* serverURL = "http://192.168.1.100:5000/api/data";

// Variables
unsigned long lastWiFiCheck = 0;
unsigned long lastDataSend = 0;
const unsigned long wifiCheckInterval = 30000;  // Check WiFi every 30 seconds
const unsigned long dataSendInterval = 2000;    // Send data every 2 seconds
bool wifiConnected = false;

void connectToWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println();
    Serial.println("WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    wifiConnected = false;
    Serial.println();
    Serial.println("WiFi connection failed!");
  }
}

void sendDataToDashboard(int rawValue, float filteredValue, float percentage) {
  if (!wifiConnected || WiFi.status() != WL_CONNECTED) {
    return;
  }

  HTTPClient http;
  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");

  // Create JSON payload
  String jsonPayload = "{";
  jsonPayload += "\"raw_value\":" + String(rawValue) + ",";
  jsonPayload += "\"filtered_value\":" + String(filteredValue, 2) + ",";
  jsonPayload += "\"percentage\":" + String(percentage, 2) + ",";
  jsonPayload += "\"timestamp\":" + String(millis());
  jsonPayload += "}";

  // Send POST request
  int httpResponseCode = http.POST(jsonPayload);
  
  if (httpResponseCode > 0) {
    Serial.print("Data sent successfully. Response code: ");
    Serial.println(httpResponseCode);
  } else {
    Serial.print("Error sending data. Response code: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
}

void setup() {
  // Start serial communication
  Serial.begin(115200);
  delay(1000);

  // Set D32 as power source
  pinMode(SENSOR_POWER_PIN, OUTPUT);
  digitalWrite(SENSOR_POWER_PIN, HIGH); // Enable power
  
  // Sensor reading pin
  pinMode(SENSOR_DATA_PIN, INPUT);

  Serial.println("PlatformIO: Sistem Baslatildi.");
  Serial.println("Initializing WiFi...");
  
  // Connect to WiFi
  connectToWiFi();
}

void loop() {
  // Check WiFi connection periodically
  unsigned long currentMillis = millis();
  if (currentMillis - lastWiFiCheck >= wifiCheckInterval) {
    lastWiFiCheck = currentMillis;
    if (WiFi.status() != WL_CONNECTED) {
      wifiConnected = false;
      Serial.println("WiFi disconnected. Attempting to reconnect...");
      connectToWiFi();
    }
  }

  // Read sensor data
  int suSeviyesi = analogRead(SENSOR_DATA_PIN);

  // Print to serial (for local monitoring)
  Serial.print("Su Seviyesi: ");
  Serial.println(suSeviyesi);

  // Send data to dashboard periodically
  if (wifiConnected && (currentMillis - lastDataSend >= dataSendInterval)) {
    lastDataSend = currentMillis;
    
    // For simplicity, we'll send raw value. 
    // The dashboard can do filtering, or you can add filtering here
    float filteredValue = suSeviyesi; // You can add filtering logic here
    float percentage = 0.0; // Dashboard will calculate this based on calibration
    
    sendDataToDashboard(suSeviyesi, filteredValue, percentage);
  }

  delay(100); // Delay to prevent overflow
}