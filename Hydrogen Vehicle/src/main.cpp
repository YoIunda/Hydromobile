#include <Arduino.h>
#include "max6675_helper.h"
#include "max6675.h"
#include "sam-m10q.h" // Add this line

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
  sam_m10q_init(); // Initialize the GNSS module
}

void loop() {
  max6675_read(thermocouple); // Make sure max6675_read takes a reference in max6675.cpp
  mq8_read();
  sam_m10q_read(); // Read and display GNSS data
  delay(5000);
}