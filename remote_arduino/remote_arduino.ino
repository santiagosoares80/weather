#include "DHT.h"
#include <RH_ASK.h>
#include <RHDatagram.h>
#include <stdlib.h>

#define DHTPIN 2     // Digital pin connected to the DHT sensor
#define DHTTYPE DHT11

#define RXPIN 13
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
RH_ASK radio(SPEED, RXPIN, TXPIN);
RHDatagram manager(radio, MYADDRESS);

//Set initial value of message id
uint8_t id = 0;

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

  //Set message ID
  manager.setHeaderId((uint8_t)id);

  //Tries 5 times to send the control message
  for (int i = 0; i < 5; i++) {
    if(!manager.sendto((uint8_t*)REBOOTMESSAGE, sizeof(REBOOTMESSAGE), SERVER)) {
      Serial.println(F("Transmission of reboot message failed!"));
      return;
    }
    
    //Waits message to be transmited
    manager.waitPacketSent();
    
    //Waits 200ms to try again
    delay(500);
  }
  
}

void loop() {

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

  //Set message ID
  manager.setHeaderId((uint8_t)id);
  
  //Set flag to temperature message
  manager.setHeaderFlags(TEMPFLAG, CLEARFLAG);
  
  // Try 5 times to transmit temperature
  for (int i = 0; i < 5; i++) {
    //Send message
    if(!manager.sendto((uint8_t*)temp, sizeof(temp), SERVER)) {
      Serial.println(F("Transmission of temperature failed!"));
      return;
    }
    //Waits message to be transmited
    manager.waitPacketSent();
    //Waits 200ms to try again
    delay(500);
  }
  
  //Set flag to humidity message
  manager.setHeaderFlags(HUMIDFLAG, CLEARFLAG);

  // Try 5 times to transmit humidity
  for (int i = 0; i < 5; i++) {
    //Send message
    if(!manager.sendto((uint8_t*)humidity, sizeof(humidity), SERVER)) {
      Serial.println(F("Transmission of humidity failed!"));
      return;
    }
    //Waits message to be transmited
    manager.waitPacketSent();  
    //Waits 200ms to try again 
    delay(500);
  }

  //Increments message id
  id++;

  // Wait a 15 minutes between measurements.
  delay(900000);
}
