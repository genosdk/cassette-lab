#include "PluginProcessor.h"
juce::AudioProcessorValueTreeState::ParameterLayout CassetteProcessor::layout() {
    juce::AudioProcessorValueTreeState::ParameterLayout p;
    p.add(std::make_unique<juce::AudioParameterFloat>(juce::ParameterID{"input_db", 1}, "Input (dB)", -24.0f, 24.0f, 0.0f));
    p.add(std::make_unique<juce::AudioParameterFloat>(juce::ParameterID{"output_db", 1}, "Output (dB)", -24.0f, 24.0f, 0.0f));
    p.add(std::make_unique<juce::AudioParameterFloat>(juce::ParameterID{"mix", 1}, "Wet mix", 0.0f, 1.0f, 1.0f));
    return p;
}
CassetteProcessor::CassetteProcessor()
 : AudioProcessor(BusesProperties().withInput("Input", juce::AudioChannelSet::stereo(), true)
                                  .withOutput("Output", juce::AudioChannelSet::stereo(), true)),
   state(*this, nullptr, "CassetteState", layout()),
   input(state.getRawParameterValue("input_db")),
   output(state.getRawParameterValue("output_db")),
   mix(state.getRawParameterValue("mix")) {}
void CassetteProcessor::prepareToPlay(double rate, int) {
    engine.prepare(rate, input->load(), output->load(), mix->load());
    setLatencySamples(0);
}
bool CassetteProcessor::isBusesLayoutSupported(const BusesLayout& b) const {
    auto out = b.getMainOutputChannelSet();
    return (out == juce::AudioChannelSet::mono() || out == juce::AudioChannelSet::stereo())
        && out == b.getMainInputChannelSet();
}
void CassetteProcessor::processBlock(juce::AudioBuffer<float>& audio, juce::MidiBuffer&) {
    juce::ScopedNoDenormals guard;
    engine.setParameters(input->load(), output->load(), mix->load());
    engine.process(audio.getArrayOfWritePointers(), audio.getNumChannels(), audio.getNumSamples());
}
void CassetteProcessor::getStateInformation(juce::MemoryBlock& data) {
    auto tree = state.copyState();
    tree.setProperty("schemaVersion", 1, nullptr);
    if (auto xml = tree.createXml()) copyXmlToBinary(*xml, data);
}
void CassetteProcessor::setStateInformation(const void* data, int size) {
    if (auto xml = getXmlFromBinary(data, size))
        if (xml->hasTagName(state.state.getType())) state.replaceState(juce::ValueTree::fromXml(*xml));
}
juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter() { return new CassetteProcessor(); }
