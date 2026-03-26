#include "Arduino.h"

byte blinkSequence[] = {0, 20, 100, 180, 255, 180, 100, 20, 0};
int sequenceSize = sizeof(blinkSequence) / sizeof(blinkSequence[0]);

class Blinker {
    public:
        Blinker(int pin, int periodMS, float brightness) {
            _pin = pin;
            _periodMS = periodMS;
            _blinkIndex = 0;
            _blinking = false;
            _lastTickMS = 0;
            _brightness = brightness;

            // Calculate highest brightness index in the sequence
            _maxBrightnessIndex = 0;
            for (int i = 0; i < sequenceSize; i++) {
                if (blinkSequence[i] > blinkSequence[_maxBrightnessIndex]) {
                    _maxBrightnessIndex = i;
                }
            }
            
            // Calculate tick interval to fit the entire sequence into the period
            _tickMS = _periodMS / sequenceSize;
        }

        void setup() {
            pinMode(_pin, OUTPUT);
            analogWrite(_pin, 0);
        }

        void tick() {
            if (!_blinking && _blinkIndex == 0) {
                return;
            }
            if (millis() - _lastTickMS >= _tickMS) {
                analogWrite(_pin, (byte)(blinkSequence[_blinkIndex] * _brightness));
                
                if (_blinking) {
                    _blinkIndex = (_blinkIndex + 1) % sequenceSize;
                } else {
                    if (_blinkIndex < _maxBrightnessIndex && _blinkIndex > 0) {
                        _blinkIndex--;
                    } else if (_blinkIndex >= _maxBrightnessIndex) {
                        _blinkIndex = (_blinkIndex + 1) % sequenceSize;
                    }
                }
                _lastTickMS = millis();
            }
        }

        void setBlinking(bool blinking) {
            _blinking = blinking;
        }

    private:
        int _pin;
        bool _blinking;
        int _blinkIndex;
        int _periodMS;
        int _tickMS;
        int _maxBrightnessIndex;
        unsigned long _lastTickMS;
        float _brightness;
};