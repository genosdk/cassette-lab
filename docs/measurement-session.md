# Marantz cassette measurement session — v0.1

Goal: characterize this physical unit and selected tape stock without confusing interface, electronics, and tape effects. The 3D revision 25 is a visual reference only, not an audio calibration. Record the model from its actual label before testing; PMD221 is the current project identification. Treat the reference path as mono unless hardware documentation and routing demonstrate otherwise. Stereo plugin processing is an extension.

## Equipment and session

Use the recorder, a known-good cassette, audio interface with a spare line output and line input, correct cables for the pictured LINE IN/OUT, and a DAW. Photograph all switch/knob settings and tape packaging. Record serial, tape brand/formulation/length, side, prior usage, power source and maintenance condition. Preserve the unit's baseline before any cleaning or adjustment; never adjust head azimuth for this session.

Create a 96 kHz session; capture WAV at 24-bit or 32-bit float, with all interface DSP, DAW inserts, normalization, warping, tempo-following and automatic gain disabled. Generated test signals are mono 24-bit PCM. Keep all original captures unedited. Set interface inputs to LINE, phantom power off. Use one output, not a stereo output summed by a passive Y cable. Keep monitoring low; route the return only to recording/monitoring, never back to the output feeding the recorder.

The generated dBFS values describe digital sine peak amplitude, not analog dBu or tape flux. They do NOT calibrate the deck's meter. If interface full-scale output voltage is unknown, log the output knob position and call it relative calibration. Measure voltages only with suitable equipment if absolute calibration is needed.

## Routing and gain calibration

1. Interface OUT → interface LINE IN: record the complete test set as the loopback baseline. Begin with the hardware output low; raise gently. Keep capture peaks at or below -6 dBFS. Fix input gain and record output settings.
2. Interface OUT → deck LINE IN; deck LINE OUT → interface LINE IN. Select LINE and disable automatic level/noise processing only where the physical switches permit; log their exact positions. Do not assume A.N.C. is a Dolby or automatic gain control. Photograph it and keep fixed for baseline.
3. Play the -18 dBFS 1 kHz reference. Adjust deck record level to its indicated 0 mark, if attainable without interface overload. Log meter reading and physical knob positions. If not attainable, retain a documented lower reference. The meter's 0 mark is an operational reference, not known tape flux.
4. Record, rewind and play back. These are separate passes; do not assume this unit supports off-tape monitoring during recording. Set playback/interface capture gain for the hottest pass, then hold it fixed for all comparisons. If any gain changes, record a new loopback/reference and start a new series.
5. For saturation tests, keep deck record gain and interface output fixed and vary only stimulus level. Stop or reduce the series if electronics or ADC clip; retain rejected files with a reason. Never normalize individual files.

## Files to generate

Run `python3 tools/generate_stimuli.py --out measurements/stimuli`.
Each file has two seconds of silence before and after signal, with 10 ms edge fades.

| Signal | Active duration | Digital peak | Purpose |
|---|---:|---:|---|
| 1 kHz reference | 10 s | -18 dBFS | Gain reference |
| Log sweep 30 Hz–20 kHz | 20 s | -30, -18, -6 dBFS | Level-dependent response; ignore bins below noise floor |
| 100 Hz / 1 kHz / 10 kHz sine | 10 s each | -30, -18, -12, -6 dBFS | Harmonic response versus level |
| 3,150 Hz sine | 60 s | -18 dBFS | Relative speed drift and pitch modulation |
| Digital silence | 60 s | zero | Noise with transport running on recorded tape |

The upper sweep limit is a probe, not a claimed deck bandwidth. Silence means actively recording a zero-valued signal, then playing that recording; also capture stopped-transport noise separately. Capture blank/unrecorded tape separately if desired, label it distinctly.

## Minimum first session

Use one known-good tape and the recorder's normal labeled speed/EQ setting. Do not assume Chrome/Metal recording support or 3¾/7½ IPS modes from the earlier concept list.

- One complete interface loopback set.
- Three record/playback takes of the reference, low-level sweep and 3,150 Hz signal.
- One complete level series of sweeps and the three sine frequencies.
- 60 seconds each: recorded silence playback, stopped deck, interface baseline.
- Two 20–30 second source excerpts you own: transient drums and sustained/pitched material. Keep one for fitting and one held out for validation. Preserve dry source and unprocessed return.
- Repeat the reference at the end to quantify session drift.

Extend later to additional tapes, supported speed/EQ settings, manual versus automatic processing, battery versus adapter, and aged media. Change one factor at a time. Record source routing and settings per take. Do not attempt stereo crosstalk measurement on a mono recorder; a stereo extension needs a separate defined model.

## Naming and record sheet

`YYYYMMDD_unit01_tape01_A_normal_line_sine1000_m18_t01_return.wav`
Use `loopback`, `return`, `stopped` and `source` suffixes. Use m18 for -18 dBFS. Record actual speed in metadata only after verifying it. Store raw WAVs outside Git; commit manifests/checksums and derived small tables. Do not convert raw recordings to MP3 or normalize them.

Fill measurements/session-template.csv. Never overwrite raw files; retain a SHA-256 manifest and separate working copies. Repeat rejected takes with incremented take numbers.

## Quality checks and analysis

Check every file for overload, missing channels, unexpected silence, dropouts and routing errors. ADC clipping invalidates harmonic measurement. Tape compression may be desired; distinguish it from converter clipping using loopback and gain records. Log capture peaks and reference level; inspect waveforms without modifying them.

Align source/return using correlation on analysis copies. Preserve original timing for wow/flutter; globally resampling or warping away drift destroys that measurement. Account for clock mismatch and tape drift when comparing sweeps. Use low-level sweeps for approximate linear response; high-level sweeps are nonlinear and should not be treated as a single linear impulse response.

Subtract interface response in the valid signal-to-noise band. Analyze tones for fundamental gain, harmonic levels, and noise; do not call all harmonics tape distortion if record electronics contribute. Analyze 3,150 Hz instantaneous frequency, remove mean frequency error separately, and report unweighted relative modulation with the analysis bandwidth and method. Do not label it standardized DIN/IEC wow/flutter without implementing the corresponding weighting and detector. This records combined record/play transport instability, not isolated playback transport.

Report noise spectrum/RMS with bandwidth, and response/distortion spread across repeated takes. Track absolute level and timing; use loudness-matched copies only for listening comparisons. Fit on one set, validate against held-out excerpts. Accept a model only after documenting its errors and repeatability; targets should follow the measured unit, not arbitrary tape-plugin defaults.

## Return package

Send original source + loopback + raw returns, completed CSV, SHA-256 manifest, photos of settings, and brief notes on audible anomalies. The next development milestone is an analysis report and a versioned calibration profile, before claiming hardware-matched DSP.
