#include <Arduino.h>

// Water level sensor - PlatformIO code
// Hardware hack: Use D32 pin as power source instead of 3.3V pin

#define SENSOR_POWER_PIN  32  // Power pin (red wire)
#define SENSOR_DATA_PIN   34  // Data pin (yellow/orange wire)

void setup() {
  // Start serial communication
  Serial.begin(115200);

  // Set D32 as power source
  pinMode(SENSOR_POWER_PIN, OUTPUT);
  digitalWrite(SENSOR_POWER_PIN, HIGH); // Enable power
  
  // Sensor reading pin
  pinMode(SENSOR_DATA_PIN, INPUT);

  Serial.println("PlatformIO: Sistem Baslatildi.");
}

void loop() {
  // Read sensor data
  int suSeviyesi = analogRead(SENSOR_DATA_PIN);

  // Print to serial
  Serial.print("Su Seviyesi: ");
  Serial.println(suSeviyesi);

  delay(100); // Delay to prevent overflow
}