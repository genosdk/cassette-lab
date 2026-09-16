#include "PluginEditor.h"
#include "CassetteArtwork.h"

namespace {
const juce::Colour ink(0xffe7e2d2), muted(0xffa3a395), gold(0xffd1b46c);
}

void CassetteEditor::DialStyle::drawRotarySlider(juce::Graphics& g, int x, int y, int w, int h,
                                                float position, float start, float end, juce::Slider&) {
    auto area = juce::Rectangle<float>(static_cast<float>(x), static_cast<float>(y),
                                       static_cast<float>(w), static_cast<float>(h)).reduced(8);
    const float radius = juce::jmin(area.getWidth(), area.getHeight()) * 0.5f;
    const auto centre = area.getCentre();
    juce::Path track, value;
    track.addCentredArc(centre.x, centre.y, radius, radius, 0, start, end, true);
    value.addCentredArc(centre.x, centre.y, radius, radius, 0, start, start + position * (end - start), true);
    g.setColour(juce::Colour(0xff44463e)); g.strokePath(track, juce::PathStrokeType(2));
    g.setColour(gold); g.strokePath(value, juce::PathStrokeType(2.5f));
    const auto dial = juce::Rectangle<float>(radius * 1.6f, radius * 1.6f).withCentre(centre);
    g.setGradientFill(juce::ColourGradient(juce::Colour(0xff52544a), dial.getTopLeft(),
                                          juce::Colour(0xff171914), dial.getBottomRight(), false));
    g.fillEllipse(dial);
    g.setColour(juce::Colour(0xff73766a)); g.drawEllipse(dial, 1);
    const float angle = start + position * (end - start);
    const auto tip = centre.getPointOnCircumference(radius * 0.64f, angle);
    const auto base = centre.getPointOnCircumference(radius * 0.35f, angle);
    g.setColour(ink); g.drawLine({base, tip}, 2.5f);
}

CassetteEditor::CassetteEditor(CassetteProcessor& p) : AudioProcessorEditor(p), processor(p) {
    setLookAndFeel(&style);
    faceplate = juce::ImageCache::getFromMemory(CassetteArtwork::pmd221reference_png,
                                               CassetteArtwork::pmd221reference_pngSize);
    auto setup = [this](juce::Slider& slider, juce::Label& label, const juce::String& name,
                       double resetValue, const juce::String& tip) {
        slider.setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
        slider.setTextBoxStyle(juce::Slider::TextBoxBelow, false, 96, 24);
        slider.setDoubleClickReturnValue(true, resetValue);
        slider.setName(name);
        slider.setTooltip(tip);
        slider.setColour(juce::Slider::textBoxTextColourId, ink);
        slider.setColour(juce::Slider::textBoxBackgroundColourId, juce::Colour(0xff1a1c17));
        slider.setColour(juce::Slider::textBoxOutlineColourId, juce::Colour(0xff484a40));
        label.setText(name.toUpperCase(), juce::dontSendNotification);
        label.setJustificationType(juce::Justification::centred);
        label.setColour(juce::Label::textColourId, ink);
        addAndMakeVisible(slider); addAndMakeVisible(label);
    };
    setup(input, inputLabel, "Input", 0, "Input gain. Double-click to reset to 0 dB.");
    setup(output, outputLabel, "Output", 0, "Output gain. Double-click to reset to 0 dB.");
    setup(mix, mixLabel, "Mix", 1, "Dry/wet blend. Double-click to reset to 100%.");
    inputAttachment = std::make_unique<Attachment>(p.parameters(), "input_db", input);
    outputAttachment = std::make_unique<Attachment>(p.parameters(), "output_db", output);
    mixAttachment = std::make_unique<Attachment>(p.parameters(), "mix", mix);
    for (auto* slider : {&input, &output}) {
        slider->textFromValueFunction = [](double v) { return juce::String(v, 1) + " dB"; };
        slider->valueFromTextFunction = [](const juce::String& s) { return s.getDoubleValue(); };
    }
    mix.textFromValueFunction = [](double v) { return juce::String(v * 100, 0) + "%"; };
    mix.valueFromTextFunction = [](const juce::String& s) { return s.getDoubleValue() / 100; };
    input.updateText(); output.updateText(); mix.updateText();
    setResizable(true, true);
    setResizeLimits(720, 660, 1200, 1100);
    if (auto* constrainer = getConstrainer()) constrainer->setFixedAspectRatio(12.0 / 11.0);
    setSize(840, 770);
    startTimerHz(30);
}

CassetteEditor::~CassetteEditor() { stopTimer(); setLookAndFeel(nullptr); }

void CassetteEditor::paint(juce::Graphics& g) {
    const float scale = static_cast<float>(getWidth()) / 840.0f;
    g.addTransform(juce::AffineTransform::scale(scale));
    g.fillAll(juce::Colour(0xff141611));
    g.setColour(ink); g.setFont(juce::FontOptions(22, juce::Font::bold));
    g.drawText("CASSETTE LAB", 24, 14, 300, 30, juce::Justification::centredLeft);
    g.setColour(muted); g.setFont(juce::FontOptions(12));
    g.drawText("UNIT 01 / PMD221", 530, 16, 286, 24, juce::Justification::centredRight);
    g.setImageResamplingQuality(juce::Graphics::highResamplingQuality);
    g.drawImageWithin(faceplate, 24, 56, 792, 528, juce::RectanglePlacement::centred);
    g.setColour(juce::Colour(0xff373a30)); g.drawHorizontalLine(598, 24, 816);
    drawMeter(g, {564, 635, 248, 16}, inLevel, "IN");
    drawMeter(g, {564, 681, 248, 16}, outLevel, "OUT");
    g.setColour(muted); g.setFont(juce::FontOptions(11));
    g.drawText("PEAK dBFS  /  PRE INPUT + POST OUTPUT", 564, 712, 248, 18, juce::Justification::centredLeft);
    g.setColour(gold);
    g.drawText("CALIBRATION MODE  /  Tape model pending measurements", 24, 741, 792, 18,
               juce::Justification::centredLeft);
}

void CassetteEditor::resized() {
    const float scale = static_cast<float>(getWidth()) / 840.0f;
    int i = 0;
    for (auto pair : {std::pair<juce::Slider*, juce::Label*>(&input, &inputLabel),
                      {&output, &outputLabel}, {&mix, &mixLabel}}) {
        const int x = 24 + i++ * 174;
        pair.first->setBounds(juce::Rectangle<float>(static_cast<float>(x), 626, 150, 106)
                                 .transformedBy(juce::AffineTransform::scale(scale)).toNearestInt());
        pair.second->setBounds(juce::Rectangle<float>(static_cast<float>(x), 606, 150, 20)
                                  .transformedBy(juce::AffineTransform::scale(scale)).toNearestInt());
    }
}

void CassetteEditor::timerCallback() {
    inLevel = processor.inputLevel(); outLevel = processor.outputLevel();
    const float scale = static_cast<float>(getWidth()) / 840.0f;
    repaint(juce::Rectangle<float>(550, 606, 280, 130).transformedBy(juce::AffineTransform::scale(scale)).toNearestInt());
}

void CassetteEditor::drawMeter(juce::Graphics& g, juce::Rectangle<float> area, float level,
                             const juce::String& name) {
    const float db = juce::Decibels::gainToDecibels(level, -60.0f);
    g.setFont(juce::FontOptions(11)); g.setColour(muted);
    g.drawText(name, area.translated(0, -19).toNearestInt(), juce::Justification::centredLeft);
    const auto text = db <= -60 ? juce::String("< -60") : juce::String(db, 1);
    g.drawText(text + " dBFS", area.translated(0, -19).toNearestInt(), juce::Justification::centredRight);
    g.setColour(juce::Colour(0xff292c23)); g.fillRect(area);
    const float fraction = juce::jlimit(0.0f, 1.0f, (db + 60) / 60);
    g.setColour(db >= 0 ? juce::Colour(0xffee624b) : gold);
    g.fillRect(area.withWidth(area.getWidth() * fraction));
    for (int tick = 1; tick < 12; ++tick) {
        g.setColour(juce::Colour(0xff141611));
        const float x = area.getX() + area.getWidth() * static_cast<float>(tick) / 12;
        g.drawVerticalLine(static_cast<int>(x), area.getY(), area.getBottom());
    }
}
