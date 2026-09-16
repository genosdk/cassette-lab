cmake_minimum_required(VERSION 3.22)
project(CassetteLab VERSION 0.1.0 LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
option(CASSETTE_BUILD_PLUGIN "Build JUCE plugin targets" ON)
include(CTest)
add_library(cassette_dsp INTERFACE)
target_include_directories(cassette_dsp INTERFACE src)
if(BUILD_TESTING)
  add_executable(cassette_tests tests/EngineTests.cpp)
  target_link_libraries(cassette_tests PRIVATE cassette_dsp)
  add_test(NAME engine COMMAND cassette_tests)
endif()
if(CASSETTE_BUILD_PLUGIN)
  include(FetchContent)
  FetchContent_Declare(JUCE GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
    GIT_TAG 51a8a6d7aeae7326956d747737ccf1575e61e209)
  FetchContent_MakeAvailable(JUCE)
  set(formats VST3 Standalone)
  if(APPLE)
    list(APPEND formats AU)
  endif()
  juce_add_plugin(CassetteLab
    COMPANY_NAME "USR" BUNDLE_ID "group.usr.cassettelab"
    PLUGIN_MANUFACTURER_CODE Usrg PLUGIN_CODE Cslt
    PRODUCT_NAME "Cassette Lab" FORMATS ${formats}
    IS_SYNTH FALSE NEEDS_MIDI_INPUT FALSE NEEDS_MIDI_OUTPUT FALSE
    IS_MIDI_EFFECT FALSE COPY_PLUGIN_AFTER_BUILD FALSE
    VST3_CATEGORIES Fx)
  target_sources(CassetteLab PRIVATE src/PluginProcessor.cpp)
  target_compile_definitions(CassetteLab PUBLIC JUCE_WEB_BROWSER=0 JUCE_USE_CURL=0
    JUCE_VST3_CAN_REPLACE_VST2=0)
  target_link_libraries(CassetteLab PRIVATE cassette_dsp juce::juce_audio_utils
    PUBLIC juce::juce_recommended_config_flags juce::juce_recommended_warning_flags)
endif()
