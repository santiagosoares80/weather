
#include <Adafruit_PCD8544.h>

#include <Adafruit_BMP280.h>

#include "DHT.h"
#include <RH_ASK.h>
#include <RHDatagram.h>
#include <stdlib.h>

#define DHTPIN 8
#define DHTTYPE DHT11

#define RXPIN 13
#define TXPIN 12
#define BTNPIN 2
#define BACKLIGHT 9
#define SPEED 2000
#define MYADDRESS 0x0D
#define SERVER 0x01
#define REBOOTMESSAGE "Probe reboot!"
#define CLEARFLAG 0xFF
#define CONTROLFLAG 0x10
#define TEMPFLAG 0x01
#define HUMIDFLAG 0x02
#define PRESSFLAG 0x07

DHT dht(DHTPIN, DHTTYPE);
RH_ASK radio(SPEED, RXPIN, TXPIN);
RHDatagram manager(radio, MYADDRESS);

Adafruit_BMP280 sensor_bmp;

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

//Set display on
boolean displayon;

void setup() {
  Serial.begin(9600);

  //Turn display backlight on for initialization
  pinMode(BACKLIGHT, OUTPUT);
  digitalWrite(BACKLIGHT, HIGH);
  
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

  //Initialize BMP280
  Serial.println(F("Initializing BMP280 sensor"));
  while (!sensor_bmp.begin(0x76))
  {
    Serial.println(F("Failed to initialize sensor!"));
    delay(1000);
  }
  
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

  // Interruption to light the display
  pinMode(BTNPIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(BTNPIN), light, FALLING);

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

  // Atmospheric pressure rectangle
  display.drawRoundRect(0, 25, 84, 23, 3, 2);
  display.setCursor(19,28); 
  display.println(F("PRESSURE"));
  display.setCursor(55,38);
  display.println(F("hPa"));
  display.setCursor(11,38);
  display.println(F("------")); 
  display.display();

  cli();//stop interrupts
  // Timer interruption to turn display off
  //set timer1 interrupt at 0.25Hz
  TCCR1A = 0;// set entire TCCR1A register to 0
  TCCR1B = 0;// same for TCCR1B
  TCNT1  = 0;//initialize counter value to 0
  // set compare match register for 0.25hz increments
  OCR1A = 62499;// = [(16*10^6) / (0.25*1024) ]- 1 (must be <65536)
  // turn on CTC mode
  TCCR1B |= (1 << WGM12);
  // Set CS10 and CS12 bits for 1024 prescaler
  TCCR1B |= (1 << CS12) | (1 << CS10);  
  // disable timer compare interrupt
  TIMSK1 |= (1 << OCIE1A);
  sei();//alLOW interrupts

  // Turns display on again after initialization of interruptions
  // It will be turned of by interruption
  digitalWrite(BACKLIGHT, HIGH);
  displayon = 1;

}
unsigned long start, ends, delta;
void loop() {

  start = millis();
  // Read humidity from DHT11
  float h = dht.readHumidity();

  // Read temperature as Celsius from BMP280
  float t = sensor_bmp.readTemperature();

  // Read atmospheric pressure from BMP280 in hPa
  float p = sensor_bmp.readPressure() / 10;

  // Failed to read any of the sensors
  if (isnan(h) || isnan(t) || isnan(p)) {
    Serial.println(F("Failed to read from sensors!"));
    return;
  }
  
  // Print to Serial 
  Serial.print(F("Humidity: "));
  Serial.print(h);
  Serial.println(F("%"));
  Serial.print(F("Temperature BMP280: "));
  Serial.print(t);
  Serial.print(F("ºC Pressure: "));
  Serial.print(p);
  Serial.println(F("hPa"));

  // Refresh display with new values
  // Temperature 
  display.fillRect(4, 13, 25 , 10, 0);
  display.setCursor(4,14);
  display.println(t,1); 
   
  // Relative humidity
  display.fillRect(50, 13, 23 , 10, 0);
  display.setCursor(50,14);
  display.println(h,1); 
   
  // Atmospheric pressure
  display.fillRect(4, 37, 50 , 10, 0);
  display.setCursor(11,38);
  display.println(p,2); 

  // Refresh display
  display.display();

  // Convert floats to strings
  char humidity[5];
  dtostrf(h, 3, 1, humidity);
  char temp[6];
  dtostrf(t, 5, 1, temp);
  char pressure[10];
  dtostrf(p, 9, 1, pressure);

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

  //Set flag to pressure message
  manager.setHeaderFlags(PRESSFLAG, CLEARFLAG);

  // Try 5 times to transmit pressure
  for (int i = 0; i < 5; i++) {
    //Send message
    if(!manager.sendto((uint8_t*)pressure, sizeof(pressure), SERVER)) {
      Serial.println(F("Transmission of pressure failed!"));
      return;
    }
    //Waits message to be transmited
    manager.waitPacketSent();  
    //Waits 500ms to try again 
    delay(500);
  }

  //Increments message id
  id++;
  ends = millis();
  delta = ends - start;
  Serial.println(delta);
  // Wait a 10 seconds between measurements.
  delay(10000);
}

//Function that turns display lights on
void light()
{
  digitalWrite(BACKLIGHT, HIGH);
  TCNT1 = 0;
  displayon = 1;
}

//Function that turn display light off after 4 seconds
ISR(TIMER1_COMPA_vect)
{
  if(displayon)
  {
    digitalWrite(BACKLIGHT, LOW);
    displayon = 0;
  }
}
