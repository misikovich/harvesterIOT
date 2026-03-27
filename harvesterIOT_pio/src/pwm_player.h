// pwm_player.h
#pragma once
#include <Arduino.h>

#define PWM_FREQ 39000
#define PWM_RESOLUTION 11 // bits
#define PWM_MAX_DUTY 2047 // 2^11 - 1

#define LEDC_CH_IN1 0
#define LEDC_CH_IN2 1

#define PIN_IN1 4
#define PIN_IN2 5