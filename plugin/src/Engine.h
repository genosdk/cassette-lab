#pragma once
#include <algorithm>
#include <cmath>
namespace cassette {
// Transparent calibration scaffold. No claimed tape response or saturation.
class Engine {
public:
    void prepare(double sampleRate, float inputDb, float outputDb, float mix) noexcept {
        rampLength = std::max(1, static_cast<int>(sampleRate * 0.02));
        current = target = gain(inputDb, outputDb, mix);
        remaining = 0;
    }
    void setParameters(float inputDb, float outputDb, float mix) noexcept {
        const float next = gain(inputDb, outputDb, mix);
        if (next != target) {
            target = next;
            remaining = rampLength;
            step = (target - current) / static_cast<float>(remaining);
        }
    }
    void process(float* const* channels, int channelCount, int samples) noexcept {
        for (int n = 0; n < samples; ++n) {
            if (remaining > 0) {
                current += step;
                if (--remaining == 0) current = target;
            }
            for (int c = 0; c < channelCount; ++c) channels[c][n] *= current;
        }
    }
private:
    static float gain(float in, float out, float mix) noexcept {
        mix = std::clamp(mix, 0.0f, 1.0f);
        return ((1.0f - mix) + mix * std::pow(10.0f, in / 20.0f))
             * std::pow(10.0f, out / 20.0f);
    }
    float current = 1, target = 1, step = 0;
    int rampLength = 1, remaining = 0;
};
}
