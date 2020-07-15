  #include "DHT.h"
#include <RH_ASK.h>
#include <stdlib.h>

#define DHTPIN 2     // Digital pin connected to the DHT sensor
#define DHTTYPE DHT11

#define RXPIN 12
#define TXPIN 12
#define SPEED 2000

DHT dht(DHTPIN, DHTTYPE);
RH_ASK radio(2000, RXPIN, TXPIN);

void setup() {
  Serial.begin(9600);
  Serial.println(F("Starting DHT11"));
  dht.begin();

  Serial.println(F("Starting Radio Driver"));
  if (!radio.init()) {
    Serial.println(F("Failed to initilize radio!"));
  }
  
}

void loop() {
  // Wait a few seconds between measurements.
  delay(1000);
  
  // Read humidity
  float h = dht.readHumidity();
  
  // Read temperature as Celsius
  float t = dht.readTemperature();

  // Failed to read sensor
  if (isnan(h) || isnan(t)) {
    Serial.println(F("Failed to read from DHT sensor!"));
    return;
  }
  
  // Print to Serial 
  Serial.print(F("Humidity: "));
  Serial.print(h);
  Serial.print(F("%  Temperature: "));
  Serial.print(t);
  Serial.println(F("°C "));

  // Convert floats to strings
  char temp[5];
  dtostrf(t, 3, 1, temp);
  char humidity[5];
  dtostrf(h, 3, 1, humidity);

  // Try to transmit temperature
  if(!radio.send((uint8_t*)temp, sizeof(temp))) {
    Serial.println(F("Transmission of temperature failed!"));
    return;
  }
  
  // Wait a little bit before transmiting humidity
  delay(200);
  
  //Try to transmit humidity
  if(!radio.send((uint8_t*)humidity, sizeof(humidity))) {
    Serial.println(F("Transmission of humidity failed!"));
    return;
  }
}
