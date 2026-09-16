#pragma once
#include "PluginProcessor.h"

class CassetteEditor final : public juce::AudioProcessorEditor, private juce::Timer {
public:
    explicit CassetteEditor(CassetteProcessor&);
    ~CassetteEditor() override;
    void paint(juce::Graphics&) override;
    void resized() override;
private:
    class DialStyle final : public juce::LookAndFeel_V4 {
    public:
        void drawRotarySlider(juce::Graphics&, int, int, int, int, float, float, float, juce::Slider&) override;
    } style;
    void timerCallback() override;
    void drawMeter(juce::Graphics&, juce::Rectangle<float>, float, const juce::String&);
    CassetteProcessor& processor;
    juce::Image faceplate;
    juce::Slider input, output, mix;
    juce::Label inputLabel, outputLabel, mixLabel;
    using Attachment = juce::AudioProcessorValueTreeState::SliderAttachment;
    std::unique_ptr<Attachment> inputAttachment, outputAttachment, mixAttachment;
    float inLevel = 0, outLevel = 0;
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(CassetteEditor)
};
