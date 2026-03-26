#include <Arduino.h>
#include <EncButton.h>
#include "blinker.h"

#define BLINK_R_MOSFET_PIN 4
#define BLINK_L_MOSFET_PIN 3
#define SW_R_BLINK_PIN 0
#define SW_L_BLINK_PIN 1
#define MTR_DRV8871_IN1_PIN 21
#define MTR_DRV8871_IN2_PIN 20
#define AUD_MAX98357_I2S_LRC_PIN 5
#define AUD_MAX98357_I2S_BCLK_PIN 6
#define AUD_MAX98357_I2S_DIN_PIN 7
#define ACCEL_ADXL345_SDA_PIN 8
#define ACCEL_ADXL345_SCL_PIN 9

// EncButton defines
#define EB_NO_COUNTER
#define EB_NO_BUFFER
#define EB_DEB_TIME 50
#define EB_HOLD_TIME 600


void setup() {
}

void loop() {
    
}