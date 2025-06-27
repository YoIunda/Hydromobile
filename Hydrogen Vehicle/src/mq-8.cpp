/*
  MQUnifiedsensor Library - reading an MQ8

  Demonstrates the use a MQ8 sensor.
  Library originally added 01 may 2019
  by Miguel A Califa, Yersson Carrillo, Ghiordy Contreras, Mario Rodriguez
 
  Added example
  modified 23 May 2019
  by Miguel Califa 

  Updated library usage
  modified 26 March 2020
  by Miguel Califa 

  Wiring:
  https://github.com/miguel5612/MQSensorsLib_Docs/blob/master/static/img/MQ_Arduino.PNG
  Please make sure arduino A0 pin represents the analog input configured on #define pin

 This example code is in the public domain.

*/

//Include the library
#include <MQUnifiedsensor.h>

//Definitions
#define placa "Arduino UNO"
#define Voltage_Resolution 5
#define pin A0 //Analog input 0 of your arduinojm
#define type "MQ-8" //MQ8
#define ADC_Bit_Resolution 10 // For arduino UNO/MEGA/NANO
#define RatioMQ8CleanAir 70   //RS / R0 = 70 ppm  
//#define calibration_button 13 //Pin to calibrate your sensor

//Declare Sensor
MQUnifiedsensor MQ8(placa, Voltage_Resolution, ADC_Bit_Resolution, pin, type);

// Remove setup() and loop(), provide functions to be called from main.cpp

void mq8_init() {
  Serial.println("MQ-8 sensor initializing...");
  MQ8.setRegressionMethod(1); //_PPM =  a*ratio^b
  MQ8.setA(976.97); MQ8.setB(-0.688); // Configure the equation to to calculate H2 concentration
  MQ8.init();   
  Serial.print("Calibrating please wait.");
  float calcR0 = 0;
  for(int i = 1; i<=10; i ++)
  {
    MQ8.update(); // Update data, the arduino will read the voltage from the analog pin
    calcR0 += MQ8.calibrate(RatioMQ8CleanAir);
    Serial.print(".");
  }
  MQ8.setR0(calcR0/10);
  Serial.println("  done!.");
  if(isinf(calcR0)) {Serial.println("Warning: Connection issue, R0 is infinite (Open circuit detected) please check your wiring and supply"); while(1);}
  if(calcR0 == 0){Serial.println("Warning: Connection issue found, R0 is zero (Analog pin shorts to ground) please check your wiring and supply"); while(1);}
  MQ8.serialDebug(true);
}

void mq8_read() {
  MQ8.update();
  float correctionFactor = 0;
  float h2ppm = MQ8.readSensor(false, correctionFactor);
  float rs = MQ8.getRS();
  float r0 = MQ8.getR0();
  float ratio = rs / r0;
  Serial.print("| Sensor Ratio (RS/R0): ");
  Serial.print(ratio, 2);
  Serial.print(" | Hydrogen Estimate (ppm): ");
  Serial.println(h2ppm, 0);
}