#include <LowPower.h>

#include <Adafruit_PCD8544.h>

#include "DHT.h"
#include <RH_ASK.h>
#include <RHDatagram.h>
#include <stdlib.h>

#define DHTPIN 8
#define DHTTYPE DHT11

#define RXPIN 13
#define TXPIN 12
#define POWERPIN 10
#define SPEED 2000
#define MYADDRESS 0x0D
#define SERVER 0x01
#define REBOOTMESSAGE "Probe reboot!"
#define CLEARFLAG 0xFF
#define CONTROLFLAG 0x10
#define TEMPFLAG 0x01
#define HUMIDFLAG 0x02


DHT dht(DHTPIN, DHTTYPE);
RH_ASK radio(SPEED, RXPIN, TXPIN);
RHDatagram manager(radio, MYADDRESS);

// Pins to display Nokia 5110
// pin 7 - Serial clock out (SCLK)
// pin 6 - Serial data out (DIN)
// pin 5 - Data/Command select (D/C)
// pin 4 - LCD chip select (CS/CE)
// pin 3 - LCD reset (RST)
Adafruit_PCD8544 display = Adafruit_PCD8544(7, 6, 5, 4, 3);

//Set initial value of message id
uint8_t id = 0;

// Great part of the code was taken from:
// https://www.filipeflop.com/blog/estacao-meteorologica-com-arduino/
// Information about interruptions from:
// https://www.instructables.com/id/Arduino-Timer-Interrupts/
// Read VCC function from:
// https://code.google.com/archive/p/tinkerit/wikis/SecretVoltmeter.wiki
// Power saving techniques:
// http://www.gammon.com.au/power


// Weather variables
float h, t;

// Battery voltage
long vcc;

// Timer counter
int counter;

//Strings to transmit using radio
char humidity[5];
char temp[6];

// 'baby', 39x23px
const unsigned char baby [] PROGMEM = {
 0x00, 0x03, 0x83, 0x80, 0x00, 0x00, 0x03, 0xff, 0x80, 0x00, 0x00, 0x03, 0x6d, 0x80, 0x00, 0x00, 
  0x03, 0x7f, 0x80, 0x00, 0x00, 0x03, 0xff, 0x80, 0x00, 0x00, 0x07, 0xef, 0xc0, 0x00, 0x00, 0x0e, 
  0x6c, 0xe0, 0x00, 0x00, 0x1c, 0x6c, 0x70, 0x00, 0x00, 0x30, 0x3c, 0x18, 0x00, 0x00, 0x30, 0x10, 
  0x18, 0x00, 0x00, 0x20, 0x00, 0x08, 0x00, 0x00, 0x60, 0x00, 0x0c, 0x00, 0x00, 0xe3, 0x83, 0x8e, 
  0x00, 0x00, 0x83, 0xc7, 0x82, 0x00, 0x00, 0xe2, 0xc6, 0x8e, 0x00, 0x00, 0x60, 0x00, 0x0c, 0x00, 
  0x00, 0x20, 0x00, 0x08, 0x00, 0x00, 0x31, 0xc7, 0x18, 0x00, 0x00, 0x30, 0xfe, 0x18, 0x00, 0x00, 
  0x1c, 0x38, 0x70, 0x00, 0x00, 0x0e, 0x00, 0xe0, 0x00, 0x00, 0x07, 0xc7, 0xc0, 0x00, 0x00, 0x01, 
  0xff, 0x00, 0x00
};

void setup() {
  Serial.begin(9600);

  //Power up radio and DHT11 sensor
  pinMode(POWERPIN, OUTPUT);
  digitalWrite(POWERPIN, LOW);
  
  Serial.println(F("Initializing Display"));
  display.begin();
  display.setContrast(40);
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(BLACK);
  display.setCursor(6,14);
  display.println(F("INITIALIZING"));
  display.setCursor(27,24);
  display.println(F("PROBE"));
  display.display();
 
  Serial.println(F("Starting DHT11"));
  dht.begin();

  Serial.println(F("Starting Radio Manager"));
  while (!manager.init()) {
    Serial.println(F("Failed to initilize manager!"));
    delay(1000);
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
    
    //Waits 500ms to try again
    delay(500);
  }

  // Draw display interface
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(BLACK);
    
  // Temperature rectangle
  display.drawRoundRect(0, 0, 44, 24, 3, 2);
  display.setCursor(11,3);
  display.println(F("TEMP"));  
  display.setCursor(5,14);
  display.println(F("----")); 
  display.setCursor(29,14);
  display.drawCircle(31, 15, 1,1);
  display.println(F(" C"));
   
  // Humidity rectangle
  display.drawRoundRect(45, 0, 39, 24, 3, 2);
  display.setCursor(50,3);  
  display.println(F("HUMID"));
  display.setCursor(50,14); 
  display.println(F("----")); 
  display.setCursor(75,14);
  display.println(F("%"));  

  // Battery rectangle
  display.drawRoundRect(0, 25, 44, 23, 3, 2);
  display.setCursor(11,28); 
  display.println(F("BATT"));
  display.setCursor(5,38);
  display.println(F("----"));
  display.setCursor(29,38);
  display.println(F("mV")); 

  // Draw baby
  display.drawBitmap(45, 25,  baby, 39, 23, BLACK);
  display.display();

}

void loop() {

  //Power up radio and DHT11 sensor and wait a little for the devices to power up
  digitalWrite(POWERPIN, LOW);
  delay(2000);

  // Read humidity from DHT11
  h = dht.readHumidity();

  // Read temperature as Celsius from BMP280
  t = dht.readTemperature();

  // Failed to read any of the
  if (isnan(h) || isnan(t)) {
    Serial.println(F("Failed to read from sensor!"));
    return;
  }

  // Read battery voltage
  vcc = readVcc();
  
  // Print to Serial 
  Serial.print(F("Humidity: "));
  Serial.print(h);
  Serial.println(F("%"));
  Serial.print(F("Temperature: "));
  Serial.print(t);
  Serial.println(F("ºC"));
  Serial.print(F("VCC: "));
  Serial.print(vcc);
  Serial.println(F("mV"));


  // Refresh display with new values
  // Temperature 
  display.fillRect(4, 13, 25 , 10, 0);
  display.setCursor(4,14);
  display.println(t,1); 
   
  // Relative humidity
  display.fillRect(50, 13, 23 , 10, 0);
  display.setCursor(50,14);
  display.println(h,1); 

  // Voltage
  display.fillRect(4, 38, 24 , 9, 0);
  display.setCursor(4,38);
  display.println(vcc,1);
  
  // Refresh display
  display.display();

  // Convert floats to strings
  dtostrf(h, 3, 1, humidity);
  dtostrf(t, 5, 1, temp);

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
    //Waits 500ms to try again
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
    //Waits 500ms to try again 
    delay(500);
  }

  //Increments message id
  id++;

  //Power down peripherals to save energy
  digitalWrite(POWERPIN, HIGH);

  counter = 0;
  while(counter < 10)
  {
    LowPower.powerDown(SLEEP_8S, ADC_OFF, BOD_OFF);
    counter++;
  }
}

long readVcc()
{ 
  long result; 
  
  // Read 1.1V reference against AVcc 
  ADMUX = _BV(REFS0) | _BV(MUX3) | _BV(MUX2) | _BV(MUX1); 
  delay(2); // Wait for Vref to settle 
  
  ADCSRA |= _BV(ADSC); 
  
  // Convert 
  while (bit_is_set(ADCSRA,ADSC)); 
  result = ADCL; 
  result |= ADCH<<8; 
  result = 1126400L / result; // Back-calculate AVcc in mV 
  return result; 
}
