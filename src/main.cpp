#include <Arduino.h>

/*
 * SU SEVİYE SENSÖRÜ - PlatformIO Kodu
 * Donanım Hack: 3.3V pini yerine D32'yi güç kaynağı yapıyoruz.
 */

#define SENSOR_POWER_PIN  32  // Kırmızı Kablo (Güç)
#define SENSOR_DATA_PIN   34  // Sarı/Turuncu Kablo (Sinyal)

void setup() {
  // 1. Seri haberleşmeyi başlat
  Serial.begin(115200);

  // 2. D32 Pinini "Güç Kaynağı" yap
  pinMode(SENSOR_POWER_PIN, OUTPUT);
  digitalWrite(SENSOR_POWER_PIN, HIGH); // Elektriği ver
  
  // 3. Sensör okuma pini
  pinMode(SENSOR_DATA_PIN, INPUT);

  Serial.println("PlatformIO: Sistem Baslatildi.");
}

void loop() {
  // Sensörden veriyi oku
  int suSeviyesi = analogRead(SENSOR_DATA_PIN);

  // Ekrana yazdır
  Serial.print("Su Seviyesi: ");
  Serial.println(suSeviyesi);

  delay(100); // Çok hızlı akmasın
}