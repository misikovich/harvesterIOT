#ifndef BLINKER_H
#define BLINKER_H

#include "Arduino.h"

class Blinker {
    public:
        // Note: setting brightness to 1.0f by default in case it's not provided
        Blinker(int pin, int periodMS, float brightness = 1.0f);

        void setup();
        void tick();
        void setBlinking(bool blinking);

    private:
        int _pin;
        bool _blinking;
        int _blinkIndex;
        int _periodMS;
        int _tickMS;
        int _maxBrightnessIndex;
        float _brightness;
        unsigned long _lastTickMS;
};

#endif
