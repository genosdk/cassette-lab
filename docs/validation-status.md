# Validation status

- Framework-free DSP compiled with GCC 13, C++17 and warnings-as-errors: PASS.
- CMake DSP-only configure/build and CTest: PASS.
- 18 generated 96 kHz / mono / 24-bit PCM WAVs: header, duration, silent padding, headroom and SHA-256 verified.
- Native macOS arm64 AU/VST3/Standalone and Windows VST3/Standalone builds plus CTest: PASS on GitHub Actions run 35065078761, commit 1b2f3c6.
- pluginval 1.0.4 strictness level 5: PASS for macOS arm64 and Windows VST3, including state, automation, editor and processing tests.
- Apple auval: PASS for aufx/Cslt/Usrg after refreshing AudioComponentRegistrar discovery on the runner.
- Validation evidence: https://github.com/genosdk/cassette-lab/actions/runs/35066643315 at commit c7df0dff16ba4403f593ff64462765fd2de3dd51.
- Steinberg standalone VST3 validator: not run; pluginval reports this optional external check as skipped.
- macOS downloads are wrapped in a ZIP before artifact upload to preserve bundle executable permissions.
- Manual DAW scan, listening, automation and project state recall: pending on the user's machine.
- Local Linux full JUCE compilation remains unavailable because development packages are missing; system package installation is restricted in this environment.
- Hardware measurements and tape DSP calibration: pending captures.

The stimulus WAVs are reproducible with tools/generate_stimuli.py. They are excluded from source control and the source archive; no lossy audio compression is used.
