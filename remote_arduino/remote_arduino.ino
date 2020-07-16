#include "DHT.h"
#include <RH_ASK.h>
#include <RHDatagram.h>
#include <stdlib.h>

#define DHTPIN 2     // Digital pin connected to the DHT sensor
#define DHTTYPE DHT11

#define RXPIN 12
#define TXPIN 12
#define SPEED 2000
#define MYADDRESS 0x0A
#define SERVER 0x01
#define REBOOTMESSAGE "REBOOT"
#define CLEARFLAG 0xFF
#define CONTROLFLAG 0x10
#define TEMPFLAG 0x01
#define HUMIDFLAG 0x02

DHT dht(DHTPIN, DHTTYPE);
RH_ASK radio(2000, RXPIN, TXPIN);
RHDatagram manager(radio, MYADDRESS);

void setup() {
  Serial.begin(9600);
  Serial.println(F("Starting DHT11"));
  dht.begin();

  Serial.println(F("Starting Radio Manager"));
  if (!manager.init()) {
    Serial.println(F("Failed to initilize manager!"));
  }

  //Set flag to control message
  manager.setHeaderFlags(CONTROLFLAG, CLEARFLAG);
  
  //Send alarm message informing reboot of the probe
  if(!manager.sendto((uint8_t*)REBOOTMESSAGE, sizeof(REBOOTMESSAGE), SERVER)) {
    Serial.println(F("Transmission of reboot message failed!"));
    return;
  }
}

void loop() {
  // Wait a few seconds between measurements.
  delay(3000);
  
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

  //Set flag to temperature message
  manager.setHeaderFlags(TEMPFLAG, CLEARFLAG);
  
  // Try to transmit temperature
  if(!manager.sendto((uint8_t*)temp, sizeof(temp), SERVER)) {
    Serial.println(F("Transmission of temperature failed!"));
    return;
  }
  
  // Wait a little bit before transmiting humidity
  delay(500);

  //Set flag to humidity message
  manager.setHeaderFlags(HUMIDFLAG, CLEARFLAG);
  
  //Try to transmit humidity
  if(!manager.sendto((uint8_t*)humidity, sizeof(humidity), SERVER)) {
    Serial.println(F("Transmission of humidity failed!"));
    return;
  }
}
