# Cassette Lab — measurement-first scaffold

Development identity only: USR / Cassette Lab; plugin IDs Usrg/Cslt must remain stable once sessions are distributed.
JUCE 8.0.6 is pinned by commit. C++17, CMake >=3.22, Xcode on macOS or Visual Studio 2022 C++ tools on Windows.
Uses JUCE's official CMake API: https://github.com/juce-framework/JUCE/blob/8.0.6/docs/CMake%20API.md

## Build on the M4 Mac

```sh
cmake -S plugin -B build -DCMAKE_BUILD_TYPE=Release -DCMAKE_OSX_ARCHITECTURES=arm64
cmake --build build --config Release --parallel 2
ctest --test-dir build -C Release --output-on-failure
```

Requires network for first JUCE fetch. Outputs: build/CassetteLab_artefacts/Release/{AU,VST3,Standalone}.
For universal Mac builds use '-DCMAKE_OSX_ARCHITECTURES=arm64;x86_64' in a fresh build directory.
Windows uses the same commands without the OSX option and builds VST3 + Standalone.
Copy .component to ~/Library/Audio/Plug-Ins/Components and .vst3 to ~/Library/Audio/Plug-Ins/VST3.
Restart the host / rescan after installation. Development builds are not signed/notarized releases.

## What works now

Mono or stereo matching buses; generic editable UI; stable automatable parameter IDs;
XML state recall; 20 ms gain smoothing; zero latency; independent framework-free DSP core.
Input gain affects wet path, output gain affects the final mix. At unity, dry and wet are identical.
There is NO tape saturation, measured EQ, wow/flutter or hiss yet. No inert controls advertise these.
Stereo host support does not imply the reference recorder is stereo.

DSP-only build: add -DCASSETTE_BUILD_PLUGIN=OFF (no JUCE download).
GitHub workflow builds macOS/Windows and uploads development artifacts once connected to a repo.
Do not ship until applicable JUCE/SDK licensing and product identity are settled.

## Acceptance before listening builds

Run DSP tests, then pluginval strictness 10 on VST3 (and AU where supported), and macOS:
`auval -v aufx Cslt Usrg`.
In Logic/Ableton/REAPER verify scan, reopen/state recall, automation, mono/stereo,
44.1/48/96/192 kHz, buffers 32–2048, offline bounce, bypass and multiple instances.
These host checks are pending, not claimed completed by CI.

## Next DSP gates

1. Analyze loopback and recorder captures; attach a versioned calibration profile.
2. Fit record/playback response and level-dependent saturation; compare held-out music at matched level.
3. Add oversampling with explicit latency and dry-path alignment; test alias rejection.
4. Add shared-transport fractional delay for wow/flutter, calibrated hiss, then dropouts.
5. Bind the existing high-resolution skin to the same parameters; 3D showcase stays separate.
