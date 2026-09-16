# Validation status

- Framework-free DSP compiled with GCC 13, C++17 and warnings-as-errors: PASS.
- CMake DSP-only configure/build and CTest: PASS.
- 18 generated 96 kHz / mono / 24-bit PCM WAVs: header, duration, silent padding, headroom and SHA-256 verified.
- Native macOS arm64 AU/VST3/Standalone and Windows VST3/Standalone builds plus CTest: PASS on GitHub Actions run 35065078761, commit 1b2f3c6.
- pluginval 1.0.4 strictness level 10: PASS for macOS arm64 and Windows VST3, including state, automation, editor and processing tests.
- Apple auval: PASS for aufx/Cslt/Usrg after refreshing AudioComponentRegistrar discovery on the runner.
- Validation evidence: https://github.com/genosdk/cassette-lab/actions/runs/35069770967 at commit f8392e842f46ce29477222456e37416bebd5259f.
- Steinberg standalone VST3 validator: not run; pluginval reports this optional external check as skipped.
- macOS downloads are wrapped in a ZIP before artifact upload to preserve bundle executable permissions.
- Native editor renders generated at 720, 840 and 1200 pixel window widths (2x PNG output). Automated editor checks pass; visual review remains pending because the artifact download returned HTTP 403 in the development environment.
- Native editor embeds the unchanged photographic master, automatable Input/Output/Mix controls, and digital input/output peak meters.
- Logic AU scan and loading as an audio effect: PASS, reported by the user on 2026-09-16 after installing the signing fix.
- Manual listening, automation, project state recall, bypass and offline bounce: pending on the user's machine.
- Complete macOS bundle signatures and signatures after ZIP extraction: PASS in run 35072133249, commit 50c06f5. AU validation also passed.
- Read-only measurement intake checker: PCM/float fixtures, channel statistics, invalid samples, duplicate detection and truncation tests PASS.
- Local Linux full JUCE compilation remains unavailable because development packages are missing; system package installation is restricted in this environment.
- Hardware measurements and tape DSP calibration: pending captures.

The stimulus WAVs are reproducible with tools/generate_stimuli.py. They are excluded from source control and the source archive; no lossy audio compression is used.
