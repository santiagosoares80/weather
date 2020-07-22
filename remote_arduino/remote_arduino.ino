#include "DHT.h"
#include <stdlib.h>
#include <VirtualWire.h>

#define DHTPIN 2     // Digital pin connected to the DHT sensor
#define DHTTYPE DHT11

#define TXPIN 12
#define SPEED 2000
#define MYADDRESS 0x0A //(ASCII code for A - 10)
#define SERVER 0x01 //(ASCII code for 1)
#define REBOOTMESSAGE "REBOOT"
#define CONTROLFLAG 0x10 //(ASCII code for A - 10) 
#define TEMPFLAG 0x01 //(ASCII code for 1)
#define HUMIDFLAG 0x02 //(ASCII code for 2)
#define ID 0x01 //(ASCII code for 0)

DHT dht(DHTPIN, DHTTYPE);

void create_packet(char *message, char flags, char *payload) {
  //Header of the packet has 4 bytes: to, from , id(not used) and flags
  char header[5] = "";

  // Creating header:
  header[0] = SERVER;
  header[1] = MYADDRESS;
  header[2] = ID;
  header[3] = flags;

  //Insert header on packet
  strcat(message, header);

  //Insert payload on packet
  strcat(message, payload);
  
}

void setup() {
  Serial.begin(9600);
  Serial.println(F("Starting DHT11"));
  dht.begin();

  Serial.println(F("Setting radio up"));
  vw_set_tx_pin(TXPIN);
  vw_setup(SPEED);

  //Create a packet
  char packet[27] = ""; 
  create_packet(packet, CONTROLFLAG, REBOOTMESSAGE);
  Serial.println(F("Transmitting control packet:"));
  Serial.write(packet, strlen(packet));
  
  //Send message
  vw_send((uint8_t*)packet, strlen(packet));
  vw_wait_tx();

  //Clean packet
  packet[0] = '\0';
}

void loop() {
  // Wait a few seconds between measurements.
  delay(3000);
  
  // Read humidity
  float h = dht.readHumidity();

  //Wait to read again
  delay(200);
  
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
  char temp[5] = "";
  dtostrf(t, 3, 1, temp);
  char humidity[5] = "";
  dtostrf(h, 3, 1, humidity);

  //Create packet
  char tpacket[27] = "";
  create_packet(tpacket, TEMPFLAG, temp);
  Serial.println(F("Transmitting tpacket:"));
  Serial.write(tpacket, strlen(tpacket));
  Serial.println("");
  //Transmit packet 
  vw_send((uint8_t *)tpacket, strlen(tpacket));
  vw_wait_tx();

  //Clear packet
  //tpacket[0] = '\0';

  delay(1000);

  //Create humidity packet
  char hpacket[27] = "";
  create_packet(hpacket, HUMIDFLAG, humidity);
  Serial.println(F("Transmitting hpacket:"));
  Serial.write(hpacket, strlen(hpacket));
  Serial.println("");
  //Transmit packet
  vw_send((uint8_t *)hpacket, strlen(hpacket));
  vw_wait_tx();

  //Clear packet
  //hpacket[0] = '\0';
}
