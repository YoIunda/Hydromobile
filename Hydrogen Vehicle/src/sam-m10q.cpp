/*
  Reading lat and long via UBX binary commands - no more NMEA parsing!
  By: Nathan Seidle
  SparkFun Electronics
  Date: January 3rd, 2019
  License: MIT. See license file for more information but you can
  basically do whatever you want with this code.

  This example shows how to query a Ublox module for its lat/long/altitude. We also
  turn off the NMEA output on the I2C port. This decreases the amount of I2C traffic 
  dramatically.

  Note: Long/lat are large numbers because they are * 10^7. To convert lat/long
  to something google maps understands simply divide the numbers by 10,000,000. We 
  do this so that we don't have to use floating point numbers.

  Leave NMEA parsing behind. Now you can simply ask the module for the datums you want!

  Feel like supporting open source hardware?
  Buy a board from SparkFun!
  ZED-F9P RTK2: https://www.sparkfun.com/products/15136
  NEO-M8P RTK: https://www.sparkfun.com/products/15005
  SAM-M8Q: https://www.sparkfun.com/products/15106

  Hardware Connections:
  Plug a Qwiic cable into the GPS and a BlackBoard
  If you don't have a platform with a Qwiic connection use the SparkFun Qwiic Breadboard Jumper (https://www.sparkfun.com/products/14425)
  Open the serial monitor at 115200 baud to see the output
*/

#include <Wire.h> //Needed for I2C to GPS
#include "SparkFun_Ublox_Arduino_Library.h" //http://librarymanager/All#SparkFun_u-blox_GNSS
#include <stdint.h>
SFE_UBLOX_GPS myGPS;

long lastTime = 0; //Simple local timer. Limits amount if I2C traffic to Ublox module.

#define AID_LAT  41.0082    // Latitude in degrees (Istanbul example)
#define AID_LON  28.9784    // Longitude in degrees
#define AID_ALT  50         // Altitude in meters
#define AID_YEAR 2025
#define AID_MONTH 6
#define AID_DAY 30
#define AID_HOUR 12
#define AID_MIN 0
#define AID_SEC 0

// Helper to send UBX message over I2C
void sendUBX(uint8_t cls, uint8_t id, uint8_t* payload, uint16_t length) {
  uint8_t sync1 = 0xB5;
  uint8_t sync2 = 0x62;
  uint8_t ck_a = 0, ck_b = 0;

  // Calculate checksum
  ck_a = cls;
  ck_b = ck_a;
  ck_a += id; ck_b += ck_a;
  ck_a += (length & 0xFF); ck_b += ck_a;
  ck_a += (length >> 8); ck_b += ck_a;
  for (uint16_t i = 0; i < length; i++) {
    ck_a += payload[i]; ck_b += ck_a;
  }

  Wire.beginTransmission(0x42); // Default I2C address for u-blox
  Wire.write(sync1);
  Wire.write(sync2);
  Wire.write(cls);
  Wire.write(id);
  Wire.write(length & 0xFF);
  Wire.write((length >> 8) & 0xFF);
  for (uint16_t i = 0; i < length; i++) {
    Wire.write(payload[i]);
  }
  Wire.write(ck_a);
  Wire.write(ck_b);
  Wire.endTransmission();
}

void sendAidIni() {
  uint8_t aidIni[48] = {0};
  // UBX-AID-INI header
  aidIni[0] = 0x01; // mask: position
  aidIni[1] = 0x02; // mask: time

  // Set ECEF X/Y/Z to zero (not used)
  int32_t ecefX = 0, ecefY = 0, ecefZ = 0;
  memcpy(&aidIni[4], &ecefX, 4);
  memcpy(&aidIni[8], &ecefY, 4);
  memcpy(&aidIni[12], &ecefZ, 4);

  // Set position (lat/lon in 1e-7 deg, alt in mm)
  int32_t lat = (int32_t)(AID_LAT * 1e7);
  int32_t lon = (int32_t)(AID_LON * 1e7);
  int32_t alt = (int32_t)(AID_ALT * 1000);
  memcpy(&aidIni[16], &lat, 4);
  memcpy(&aidIni[20], &lon, 4);
  memcpy(&aidIni[24], &alt, 4);

  // Set time
  uint16_t year = AID_YEAR;
  uint8_t month = AID_MONTH;
  uint8_t day = AID_DAY;
  uint8_t hour = AID_HOUR;
  uint8_t min = AID_MIN;
  uint8_t sec = AID_SEC;
  memcpy(&aidIni[28], &year, 2);
  aidIni[30] = month;
  aidIni[31] = day;
  aidIni[32] = hour;
  aidIni[33] = min;
  aidIni[34] = sec;

  // Send UBX-AID-INI
  sendUBX(0x0B, 0x01, aidIni, 48);
  Serial.println("UBX-AID-INI (time/position aiding) sent.");
}

void sam_m10q_init() {
  Serial.println("SparkFun Ublox Example");
  Wire.begin(); //Start the I2C port. Uses default SDA and SCL pins for your board
  if (myGPS.begin() == false) //Connect to the Ublox module using Wire port
  {
    Serial.println(F("Ublox GPS not detected at default I2C address. Please check wiring. Freezing."));
    while (1);
  }
  myGPS.setI2COutput(COM_TYPE_UBX); //Set the I2C port to output UBX only (turn off NMEA noise)
  myGPS.saveConfiguration(); //Save the current settings to flash and BBR

  sendAidIni();
}

void sam_m10q_read() {
  if (millis() - lastTime > 1000) {
    lastTime = millis();
    long speed_mm_s = myGPS.getGroundSpeed();
    int speed_kmh = (int)((speed_mm_s / 1000.0) * 3.6);
    Serial.print(speed_kmh);
    Serial.println(F(" km/h"));
  }
}
