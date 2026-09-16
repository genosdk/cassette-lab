# Validation status

- Framework-free DSP compiled with GCC 13, C++17 and warnings-as-errors: PASS.
- CMake DSP-only configure/build and CTest: PASS.
- 18 generated 96 kHz / mono / 24-bit PCM WAVs: header, duration, silent padding, headroom and SHA-256 verified.
- JUCE native plugin build: pending; this Linux environment lacks required audio/windowing development packages.
- macOS AU and Windows/macOS VST3 host scan, state recall, automation, auval and pluginval: pending platform builds.
- GitHub Actions workflow included but not run remotely; no Git remote configured and connected GitHub search returned no Marantz repository under genosdk.
- Hardware measurements and tape DSP calibration: pending captures.

The stimulus WAVs are reproducible with tools/generate_stimuli.py. They are excluded from source control and the source archive; no lossy audio compression is used.
