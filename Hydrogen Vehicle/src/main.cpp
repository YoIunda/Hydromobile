#include <Arduino.h>
#include "max6675_helper.h"
#include "max6675.h"

// Declare MQ-8 functions
void mq8_init();
void mq8_read();

// Define the pins for the MAX6675 module
int thermoSO = 4;
int thermoCS = 5;
int thermoSCK = 6;

MAX6675 thermocouple(thermoSCK, thermoCS, thermoSO);

void setup() {
  Serial.begin(9600);
  delay(5000);
  max6675_init();
  mq8_init();
}

void loop() {
  max6675_read(thermocouple); // Make sure max6675_read takes a reference in max6675.cpp
  mq8_read();
  delay(5000);
}