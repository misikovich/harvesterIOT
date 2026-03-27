#include <Arduino.h>
#include <EncButton.h>

// #define BLINK_R_MOSFET_PIN 4
// #define BLINK_L_MOSFET_PIN 3
// #define SW_R_BLINK_PIN 0
// #define SW_L_BLINK_PIN 1
#define MTR_DRV8871_PIN_IN1 21
#define MTR_DRV8871_PIN_IN2 20

#define AUD_MAX98357_I2S_PIN_LRC UNDEF
#define AUD_MAX98357_I2S_PIN_BCLK UNDEF
#define AUD_MAX98357_I2S_PIN_DIN UNDEF

#define AUD_PWM_DRV8871_PIN_IN1 UNDEF
#define AUD_PWM_DRV8871_PIN_IN2 UNDEF

#define ACCEL_ADXL345_PIN_SDA 8
#define ACCEL_ADXL345_PIN_SCL 9

#define STATUS_LED_WS2812B_PIN_DATA UNDEF
#define STATUS_LED_WS2812B_NUM 2

// EncButton defines
#define EB_NO_COUNTER
#define EB_NO_BUFFER
#define EB_DEB_TIME 50
#define EB_HOLD_TIME 600

void setup() {}

void loop() {}