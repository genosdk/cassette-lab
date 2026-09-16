#include "PluginProcessor.h"

// CI-only preview tool: renders the actual native editor, not a mockup.
class Preview final : public juce::JUCEApplication {
public:
    const juce::String getApplicationName() override { return "CassettePreview"; }
    const juce::String getApplicationVersion() override { return "0.1.0"; }
    void initialise(const juce::String&) override {
        processor = std::make_unique<CassetteProcessor>();
        editor.reset(processor->createEditor());
        editor->setVisible(true);
        juce::Timer::callAfterDelay(500, [this] {
            const auto directory = juce::File::getCurrentWorkingDirectory().getChildFile("ui-preview");
            bool ok = directory.createDirectory().wasOk();
            for (const int width : {720, 840, 1200}) {
                editor->setSize(width, width * 11 / 12);
                auto snapshot = editor->createComponentSnapshot(editor->getLocalBounds(), true, 2.0f);
                auto stream = directory.getChildFile("editor-" + juce::String(width) + ".png").createOutputStream();
                ok = stream != nullptr && juce::PNGImageFormat().writeImageToStream(snapshot, *stream) && ok;
            }
            setApplicationReturnValue(ok ? 0 : 1);
            quit();
        });
    }
    void shutdown() override { editor.reset(); processor.reset(); }
private:
    std::unique_ptr<CassetteProcessor> processor;
    std::unique_ptr<juce::AudioProcessorEditor> editor;
};
START_JUCE_APPLICATION(Preview)
