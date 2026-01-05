#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

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

// Constants
const unsigned long wifiCheckInterval = 30000;  // Check WiFi every 30 seconds
const unsigned long dataSendInterval = 2000;    // Send data every 2 seconds
const unsigned long httpTimeout = 5000;         // HTTP timeout in milliseconds
const int maxWiFiAttempts = 20;                 // Maximum WiFi connection attempts

// Variables
unsigned long lastWiFiCheck = 0;
unsigned long lastDataSend = 0;
bool wifiConnected = false;
int consecutiveFailures = 0;
const int maxConsecutiveFailures = 5;  // Reset WiFi after 5 consecutive failures

void connectToWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();  // Disconnect any existing connection
  delay(100);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < maxWiFiAttempts) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    consecutiveFailures = 0;  // Reset failure counter
    Serial.println();
    Serial.println("WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    wifiConnected = false;
    consecutiveFailures++;
    Serial.println();
    Serial.print("WiFi connection failed! (Attempt ");
    Serial.print(attempts);
    Serial.println(")");
    
    if (consecutiveFailures >= maxConsecutiveFailures) {
      Serial.println("Too many failures. Resetting WiFi...");
      WiFi.disconnect();
      delay(1000);
      consecutiveFailures = 0;
    }
  }
}

void sendDataToDashboard(int rawValue, float filteredValue, float percentage) {
  if (!wifiConnected || WiFi.status() != WL_CONNECTED) {
    return;
  }

  HTTPClient http;
  
  // Configure HTTP client with timeout
  http.begin(serverURL);
  http.setTimeout(httpTimeout);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Connection", "close");  // Close connection after request

  // Create JSON payload using ArduinoJson (more reliable than string concatenation)
  StaticJsonDocument<200> doc;
  doc["raw_value"] = rawValue;
  doc["filtered_value"] = filteredValue;
  doc["percentage"] = percentage;
  
  // Handle millis() overflow (happens after ~49 days)
  unsigned long currentMillis = millis();
  doc["timestamp"] = currentMillis;

  String jsonPayload;
  serializeJson(doc, jsonPayload);

  // Send POST request
  int httpResponseCode = http.POST(jsonPayload);
  
  if (httpResponseCode > 0) {
    if (httpResponseCode == 200) {
      Serial.print("Data sent successfully. Response code: ");
      Serial.println(httpResponseCode);
      consecutiveFailures = 0;  // Reset failure counter on success
    } else {
      Serial.print("Warning: Unexpected response code: ");
      Serial.println(httpResponseCode);
    }
  } else {
    Serial.print("Error sending data. Response code: ");
    Serial.println(httpResponseCode);
    consecutiveFailures++;
    
    // If too many failures, mark WiFi as disconnected to trigger reconnection
    if (consecutiveFailures >= maxConsecutiveFailures) {
      Serial.println("Too many HTTP failures. Will reconnect WiFi.");
      wifiConnected = false;
    }
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
  // Handle millis() overflow (happens after ~49 days)
  unsigned long currentMillis = millis();
  
  // Check WiFi connection periodically (handle overflow)
  if (currentMillis - lastWiFiCheck >= wifiCheckInterval || 
      currentMillis < lastWiFiCheck) {  // Overflow detected
    lastWiFiCheck = currentMillis;
    if (WiFi.status() != WL_CONNECTED) {
      wifiConnected = false;
      Serial.println("WiFi disconnected. Attempting to reconnect...");
      connectToWiFi();
    }
  }

  // Read sensor data
  int suSeviyesi = analogRead(SENSOR_DATA_PIN);
  
  // Validate sensor reading (ESP32 ADC range is 0-4095)
  if (suSeviyesi < 0) suSeviyesi = 0;
  if (suSeviyesi > 4095) suSeviyesi = 4095;

  // Print to serial (for local monitoring)
  Serial.print("Su Seviyesi: ");
  Serial.println(suSeviyesi);

  // Send data to dashboard periodically (handle overflow)
  if (wifiConnected && 
      (currentMillis - lastDataSend >= dataSendInterval || 
       currentMillis < lastDataSend)) {  // Overflow detected
    lastDataSend = currentMillis;
    
    // For simplicity, we'll send raw value. 
    // The dashboard can do filtering, or you can add filtering here
    float filteredValue = suSeviyesi; // You can add filtering logic here
    float percentage = 0.0; // Dashboard will calculate this based on calibration
    
    sendDataToDashboard(suSeviyesi, filteredValue, percentage);
  }

  delay(100); // Delay to prevent overflow
}