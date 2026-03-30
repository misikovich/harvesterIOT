#include "pwm_player.h"
#include "stdint.h"
#include <Arduino.h>

typedef struct Waveform {
  const int16_t *data;
  uint32_t len;
  uint32_t sampleRate;
  uint8_t channels;
  uint8_t bitsPerSample;
} Waveform;

typedef struct PlaybackState {
  Waveform *waveform;
  uint32_t index;
  unsigned long start_us;
  int8_t volume;
  bool playing;
} PlaybackState;

class PwmPlayer {
private:
  int _pinIn1;
  int _pinIn2;
  int _pwmFreq;
  PlaybackState _playbackState;

	static void write_sample(uint8_t raw, uint8_t volume) {
    // center around 0:  -128 … +127
    int16_t s = (int16_t)raw - 128;

    // integer volume scale (volume 128 = no attenuation)
    s = (s * volume) >> 7;

    uint32_t duty_in1 = 0;
    uint32_t duty_in2 = 0;

    if (s > 0) {
        duty_in1 = ((uint32_t)s * PWM_MAX_DUTY) / 127;
    } else if (s < 0) {
        duty_in2 = ((uint32_t)(-s) * PWM_MAX_DUTY) / 128;
    }
    // s == 0 → both 0 → H-bridge coasts (correct, avoids brake-mode heating)

    // Core 2.x:
    ledcWrite(LEDC_CH_IN1, duty_in1, _pwmFreq);
    ledcWrite(LEDC_CH_IN2, duty_in2, _pwmFreq);

    // Core 3.x — swap to:
    // ledcWrite(PIN_IN1, duty_in1);
    // ledcWrite(PIN_IN2, duty_in2);
}

public:
  PwmPlayer(int pinIn1, int pinIn2, int pwmFreq) {
    _pinIn1 = pinIn1;
    _pinIn2 = pinIn2;
    _pwmFreq = pwmFreq;
  }

  void init() {
    pinMode(_pinIn1, OUTPUT);
    pinMode(_pinIn2, OUTPUT);
  }

  void play(Waveform *waveform, int8_t volume) {
    _playbackState.waveform = waveform;
    _playbackState.index = 0;
    _playbackState.start_us = micros();
    _playbackState.volume = volume;
  }

  void tick() {
    if (!(_playbackState.playing)) {
      return;
    }
		

  }
};
