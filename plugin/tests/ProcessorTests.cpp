#include "PluginProcessor.h"
#include <cstdlib>
#include <iostream>
#include <vector>

namespace {
void check(bool ok, const char* message) {
    if (!ok) { std::cerr << message << '\n'; std::exit(1); }
}
void set(CassetteProcessor& p, const char* id, float value) {
    auto* parameter = p.parameters().getParameter(id);
    check(parameter != nullptr, "Missing stable parameter ID");
    parameter->setValueNotifyingHost(parameter->convertTo0to1(value));
}
void settings(CassetteProcessor& p) {
    set(p, "input_db", 6.0f); set(p, "output_db", -3.0f); set(p, "mix", 0.375f);
}
void verifySettings(CassetteProcessor& p) {
    check(std::abs(p.parameters().getRawParameterValue("input_db")->load() - 6.0f) < 1e-5f, "Input recall failed");
    check(std::abs(p.parameters().getRawParameterValue("output_db")->load() + 3.0f) < 1e-5f, "Output recall failed");
    check(std::abs(p.parameters().getRawParameterValue("mix")->load() - 0.375f) < 1e-5f, "Mix recall failed");
}
void buses(CassetteProcessor& p, int channels) {
    auto layout = p.getBusesLayout();
    layout.inputBuses.set(0, juce::AudioChannelSet::canonicalChannelSet(channels));
    layout.outputBuses.set(0, juce::AudioChannelSet::canonicalChannelSet(channels));
    check(p.setBusesLayout(layout), "Supported bus layout rejected");
}
std::vector<float> render(double rate, int channels, int blockSize, bool offline) {
    CassetteProcessor p;
    buses(p, channels); p.setNonRealtime(offline); p.prepareToPlay(rate, blockSize);
    constexpr int total = 8192, change = 4096;
    std::vector<float> output(static_cast<size_t>(total * channels));
    juce::MidiBuffer midi;
    for (int start = 0; start < total;) {
        if (start == change) settings(p);
        const int boundary = start < change ? change : total;
        const int count = std::min(blockSize, boundary - start);
        juce::AudioBuffer<float> audio(channels, count);
        for (int c = 0; c < channels; ++c)
            for (int n = 0; n < count; ++n)
                audio.setSample(c, n, c == 0 ? 0.25f : -0.125f);
        p.processBlock(audio, midi);
        for (int c = 0; c < channels; ++c)
            for (int n = 0; n < count; ++n) {
                const float sample = audio.getSample(c, n);
                check(std::isfinite(sample), "Nonfinite output");
                if (start < change) check(sample == (c == 0 ? 0.25f : -0.125f), "Default processing not transparent");
                output[static_cast<size_t>(c * total + start + n)] = sample;
            }
        start += count;
    }
    const float gain = (0.625f + 0.375f * std::pow(10.0f, 6.0f/20.0f)) * std::pow(10.0f, -3.0f/20.0f);
    for (int c = 0; c < channels; ++c)
        check(std::abs(output[static_cast<size_t>((c+1)*total-1)] - gain * (c == 0 ? 0.25f : -0.125f)) < 1e-5f, "Final automated gain incorrect");
    check(p.getLatencySamples() == 0, "Unexpected latency");
    juce::AudioBuffer<float> empty(channels, 0); p.processBlock(empty, midi);
    p.releaseResources();
    return output;
}
}
int main() {
    juce::ScopedJuceInitialiser_GUI init;
    CassetteProcessor original; settings(original);
    juce::MemoryBlock state; original.getStateInformation(state);
    CassetteProcessor restored;
    restored.setStateInformation(state.getData(), static_cast<int>(state.getSize()));
    verifySettings(restored);
    const char invalid[] = "not a plugin state";
    restored.setStateInformation(invalid, sizeof(invalid)); verifySettings(restored);
    for (double rate : {44100., 48000., 96000., 192000.})
        for (int channels : {1, 2}) {
            const auto reference = render(rate, channels, 37, false);
            for (int size : {32, 512, 2048}) {
                const auto bounced = render(rate, channels, size, true);
                check(reference.size() == bounced.size(), "Render length mismatch");
                for (size_t n = 0; n < reference.size(); ++n)
                    check(std::abs(reference[n] - bounced[n]) < 1e-6f, "Realtime/offline block rendering differs");
            }
        }
    std::cout << "State recall, invalid state rejection, transparency, automation, mono/stereo and offline equivalence passed\n";
}
