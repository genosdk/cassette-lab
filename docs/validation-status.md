# Validation status

## Synthetic sweep magnitude — 2026-09-17

- Added read-only whole-record spectral magnitude comparison with input hashes, reference-excitation masking and explicit limitations.
- All 39 tooling tests PASS locally. Six new tests cover analytical FIR response, delay/polarity/gain, weak excitation, zero return, small additive noise, invalid input, sample-rate mismatch and preserved WAV bytes.
- This validates numerical behavior under synthetic conditions. Actual recorder response, capture quality and tape drift require hardware recordings; no plugin processing or artwork changed.

## Synthetic noise spectrum — 2026-09-17

- Added read-only unweighted Welch PSD, AC RMS and selected-band RMS analysis with explicit units, bin edges, DC treatment and tail reporting.
- All 33 tooling tests PASS locally. New tests cover white noise, analytically filtered noise, 60 Hz hum, Parseval/Nyquist scaling, silence, invalid inputs and preserved WAV bytes.
- No tape-noise profile or standardized weighted noise measurement is claimed. Plugin audio and artwork are unchanged.

## Synthetic carrier tracking — 2026-09-16

- Added read-only windowed frequency estimation and drift tracking.
- All 27 tooling tests PASS locally, including known stationary offset, linear drift, slow modulation, dropout/noise/boundary rejection and unchanged input bytes.
- Summary is withheld when any window fails. Reported frequency deviation is window-averaged and is not standardized wow/flutter. No plugin processing or artwork changed.

## Synthetic tone analysis — 2026-09-16

- Added stationary-tone harmonic fitting and discrete return/reference gain comparison. No plugin DSP or artwork changed.
- All 21 tooling tests PASS locally. Known cubic harmonics and two-tap filter response at 100 Hz, 1 kHz and 10 kHz match analytical results.
- Tests cover phase/DC/noninteger cycles, noise, wrong frequency, Nyquist omissions, invalid segments and WAV byte preservation.
- Requires a supplied stationary fundamental; drift estimation and continuous sweep response are not implemented. Partial harmonic THD and residual are explicitly distinguished from standardized THD+N.

## Synthetic alignment tooling — 2026-09-16

- Added read-only integer-delay/polarity/relative-gain analysis for mono PCM WAV pairs, with input hashes and ambiguity checks.
- All 15 tooling tests PASS locally. New synthetic fixtures recover known delays, gains and polarity; reject ambiguous/unrelated signals and invalid input; and verify original WAV bytes are preserved.
- NumPy 2.3.5 is pinned for optional analysis and installed by the measurement-tool CI workflow. Generation/intake remain standard-library-only.
- No physical recorder response is inferred from these synthetic tests. Fractional delay, drift tracking and response/distortion analysis remain future gates.

## Measurement preparation — 2026-09-16

- Added read-only stimulus-set verification and overwrite protection for signal generation.
- All 10 Python measurement-tool tests PASS locally, including altered audio, invalid manifests, duplicate/path entries, incorrect headers/padding and overwrite refusal.
- Existing complete 18-file 96 kHz stimulus set PASS; regenerated reference WAV is byte-identical to the prior generator output.
- Dedicated Python 3.11 CI workflow added. No plugin processing, skin or original recordings changed; generated audio remains excluded from Git.
- Hardware response fitting, saturation calibration and measured wow/flutter/noise still require captures. The analysis implementation can continue against synthetic fixtures before captures arrive; such tests cannot validate a match to the physical recorder.

## Approved temporary skin build — 2026-09-16

- Commit f65a59274d9331377f5f2b57f2939d6e396004c5: macOS arm64 and Windows builds PASS in https://github.com/genosdk/cassette-lab/actions/runs/35079854011.
- Engine and processor tests PASS on both platforms: saved settings, invalid-state rejection, unity gain within 1e-7 absolute sample error, automation, mono/stereo and realtime/offline equivalence at 44.1/48/96/192 kHz.
- Corrected two test assumptions: Mix uses 0.01 steps, and ARM fused arithmetic can round nominal zero dB during JUCE range snapping. Production processing and parameter IDs were unchanged.
- pluginval strictness 10 PASS on both platforms; Apple auval PASS; complete macOS signatures and signatures after ZIP extraction PASS.
- Approved IMG_0483.png skin preserved at 1536 x 1024; local and GitHub blob SHA match: acf2f38ff9cc0ad928f071acacdd22bdbe31f71a.
- Native editor previews rendered at all three sizes. Visual inspection remains pending because preview download returned HTTP 403 in this environment.
- macOS artifact: https://github.com/genosdk/cassette-lab/actions/runs/35079854011/artifacts/10439698512.
- Updated build still needs user review in Logic; tape DSP remains pending hardware measurements.

## Previous validation history

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
