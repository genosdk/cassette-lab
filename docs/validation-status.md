# Validation status

- Framework-free DSP compiled with GCC 13, C++17 and warnings-as-errors: PASS.
- CMake DSP-only configure/build and CTest: PASS.
- 18 generated 96 kHz / mono / 24-bit PCM WAVs: header, duration, silent padding, headroom and SHA-256 verified.
- Native macOS arm64 AU/VST3/Standalone and Windows VST3/Standalone builds plus CTest: PASS on GitHub Actions run 35065078761, commit 1b2f3c6.
- CI now runs pluginval 1.0.4 at strictness level 5 for VST3 on both platforms and Apple's auval for AU; initial results pending.
- macOS downloads are wrapped in a ZIP before artifact upload to preserve bundle executable permissions.
- Manual DAW scan, listening, automation and project state recall: pending on the user's machine.
- Local Linux full JUCE compilation remains unavailable because development packages are missing; system package installation is restricted in this environment.
- Hardware measurements and tape DSP calibration: pending captures.

The stimulus WAVs are reproducible with tools/generate_stimuli.py. They are excluded from source control and the source archive; no lossy audio compression is used.
