// this example is public domain. enjoy!
// https://learn.adafruit.com/thermocouple/

#include "max6675.h"

// Remove global variable definitions from this file. Use the instance from main.cpp.
// Provide init and read functions that accept a reference to the thermocouple object.

void max6675_init() {
  Serial.println("MAX6675 test");
  // wait for MAX chip to stabilize
  delay(5000);
}

void max6675_read(MAX6675& thermocouple) {
  Serial.print("C = "); 
  Serial.println(thermocouple.readCelsius(), 3); // Print with 3 decimal places
}