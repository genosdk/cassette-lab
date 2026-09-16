#pragma once
#include <juce_audio_utils/juce_audio_utils.h>
#include "Engine.h"
class CassetteProcessor final : public juce::AudioProcessor {
public:
    CassetteProcessor();
    void prepareToPlay(double, int) override;
    void releaseResources() override {}
    bool isBusesLayoutSupported(const BusesLayout&) const override;
    void processBlock(juce::AudioBuffer<float>&, juce::MidiBuffer&) override;
    juce::AudioProcessorEditor* createEditor() override;
    juce::AudioProcessorValueTreeState& parameters() noexcept { return state; }
    float inputLevel() const noexcept { return inputPeak.load(std::memory_order_relaxed); }
    float outputLevel() const noexcept { return outputPeak.load(std::memory_order_relaxed); }
    bool hasEditor() const override { return true; }
    const juce::String getName() const override { return "Cassette Lab"; }
    bool acceptsMidi() const override { return false; }
    bool producesMidi() const override { return false; }
    bool isMidiEffect() const override { return false; }
    double getTailLengthSeconds() const override { return 0; }
    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram(int) override {}
    const juce::String getProgramName(int) override { return {}; }
    void changeProgramName(int, const juce::String&) override {}
    void getStateInformation(juce::MemoryBlock&) override;
    void setStateInformation(const void*, int) override;
private:
    juce::AudioProcessorValueTreeState state;
    std::atomic<float> *input, *output, *mix;
    cassette::Engine engine;
    std::atomic<float> inputPeak {0}, outputPeak {0};
    float inputEnvelope = 0, outputEnvelope = 0;
    double meterSampleRate = 44100;
    static juce::AudioProcessorValueTreeState::ParameterLayout layout();
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(CassetteProcessor)
};
