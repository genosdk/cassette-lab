# Returned measurement intake

The partner's Ableton recording instructions are unchanged. This tool is for us after receiving their files; the partner does not need Python or GitHub.

Keep the original returned folder intact. With Python 3.11 or newer, run from the repository root:

```sh
python tools/check_captures.py /path/to/returned-recordings > capture-report.json
```

The tool scans WAV files recursively, computes SHA-256 checksums and reports duration, format, sample rate, channels, per-channel peak/RMS/DC offset, full-scale sample counts, nonfinite samples and byte-identical duplicates. It does not modify, normalize, resample or rename audio. PCM 16/24/32-bit and IEEE float 32-bit RIFF WAV are supported, including matching extensible subtypes. RF64, compressed audio and other formats produce explicit errors. Exit code 1 means unreadable/unsupported files or no WAV files; warnings remain review items and do not change the exit code.

Review warnings in context: intentional silence is valid, stereo needs a routing check, and full-scale samples suggest possible digital clipping rather than proving analog tape clipping. Floating-point values above unity are reported, not discarded. RMS/DC include the entire file and silence padding; files with nonfinite samples are unsuitable for calibration. A null peak_dbfs means digital silence. Duplicate checking compares complete file bytes, not just audio samples.

Compare the inventory with the partner's completed checklist and session notes. This tool does not establish session completeness, correct routing, tape playback provenance, or correct stimulus identity. Preserve loopbacks, recorder returns, level settings and dry music references separately. Resolve missing takes and routing issues before fitting a model. Alignment, frequency response, distortion and wow/flutter analysis are the next gate once actual captures are available.

## Read-only alignment candidate

Install the optional analysis dependency with `python3 -m pip install -r tools/requirements-analysis.txt` (Python 3.11+). Then run:

```sh
python3 tools/analyze_alignment.py source.wav return.wav --max-delay 2 > alignment-report.json
```

This first analysis stage accepts mono PCM 16/24/32-bit WAV pairs at the same sample rate. Float WAV and stereo captures remain supported by the intake inventory, but require a later extension of this alignment reader. Keep original captures intact; do not convert them just to satisfy this tool.

Positive delay means the return is later than the source. The report includes input checksums, integer-sample delay, signed correlation, polarity, overlap length and relative least-squares gain after removing DC. Gain is emitted only for accepted candidates. It does not write, shift, normalize, resample or warp either recording. It loads the files and FFT buffers into memory; start with individual takes, not a whole-session recording.

The method uses zero-mean correlation normalized over each overlapping region, with at least half the shorter file overlapping. The current heuristic accepts absolute correlation >=0.8, rejects a second peak >=95% of the best peak outside a 1 ms neighborhood, and flags peaks on the search boundary. Exit 0 means an accepted candidate, 2 means a candidate requiring review, and 1 means an input/analysis error. These thresholds are provisional tooling checks, not validated tape acceptance criteria. Broadband sweeps or source excerpts are preferable; repetitive tones cannot reliably identify a unique delay. Review clipping with the intake tool before analysis.

Synthetic tests cover positive/negative/zero delays, polarity inversion, gain/DC/noise, ambiguous tones, unrelated signals, search boundaries, invalid audio, PCM decoding, rate mismatch and preservation of file bytes. This establishes the tool's behavior on known fixtures only. Real tape can drift in speed, distort and decorrelate; a single global lag and gain do not measure clock drift, fractional delay, frequency response, saturation or wow/flutter, and do not establish hardware calibration.

## Logic host checks still needed

The user confirmed AU loading as an effect on 2026-09-16. At Input 0 dB, Output 0 dB and Mix 100%, the current scaffold should sound transparent. Compare bypass at matched level. Then automate Input/Output/Mix, save and reopen a project with nondefault settings, try mono and stereo instances, and compare realtime playback with an offline bounce. Record Logic/macOS versions, sample rate, buffer size and any differences. Successful loading alone does not establish these results.

## Stationary tone harmonics and discrete response points

`analyze_tone.py` uses the same optional NumPy dependency and mono PCM reader as alignment. Select an explicitly known steady portion, excluding silence, fades and transport settling:

```sh
python3 tools/analyze_tone.py return.wav --frequency 1000 --start 3 --duration 1
python3 tools/analyze_tone.py return.wav --frequency 1000 --start 3 --duration 1 --reference loopback.wav --reference-start 3
```

Times above are examples, not automatically discovered offsets. The supplied frequency must match the actual stationary fundamental; the tool does not estimate frequency or track tape drift. Reference and return segments may start at different times, must have equal requested duration and matching sample rates, and need at least 20 cycles. The tool does not alter either WAV and records full-file SHA-256 hashes and selected segment times.

A simultaneous least-squares fit estimates DC and sine/cosine components at the fundamental and harmonics (default orders 1–5, configurable to 20). It handles noninteger cycle counts at the correct frequency without treating window leakage as distortion. Harmonics at or above Nyquist are explicitly omitted. `thd_ratio` is the root-sum-square amplitude of only the reported higher harmonics divided by the fundamental; it is null when no higher harmonic can be measured. Multiply the ratio by 100 for percent. This is partial THD, not a standardized full-band THD+N result. A fitted residual includes noise, unmodeled harmonics, drift and frequency error; it must not be called tape hiss.

The optional reference reports the return/reference fundamental ratio in dB at this one frequency. Repeating with the 100 Hz, 1 kHz and 10 kHz recordings produces discrete response points, not a continuous sweep response. Comparing to a loopback removes its fundamental gain at that frequency only; it does not isolate tape distortion from electronics or subtract the reference's harmonics.

A residual above 5% of fundamental RMS marks the fit for review and suppresses a pair's gain result. This is a provisional diagnostic threshold, not a calibration acceptance criterion. Exit codes are 0 for an accepted fit, 2 for review and 1 for invalid input. Review clipping with the intake inventory first. All reported values on a review result are diagnostic only. Long segments use memory proportional to their length and harmonic count; start with a one-second stationary portion.

Synthetic validation covers known DC/phase/harmonics with noninteger cycles, an analytically derived cubic distortion spectrum, a known two-tap filter at three frequencies, injected noise, wrong frequency, Nyquist omissions, invalid input and unchanged WAV bytes. These fixtures do not establish accuracy on drifting physical tape. Frequency estimation/drift tracking and continuous sweep analysis remain later work.

## Windowed frequency and drift tracking

```sh
python3 tools/analyze_drift.py speed-return.wav --start 3 --duration 10 --nominal 3150 --search-hz 100 --window 0.1 --hop 0.05
```

Choose an active segment; the example does not discover transport start. The mono PCM reader and NumPy dependency are shared with the other analyzers. Original files remain unchanged, and the report includes a SHA-256 checksum and segment start time. Window center times are relative to that segment. Any incomplete trailing window is omitted and its sample count reported.

For each Hann-windowed segment, an FFT finds a spectral peak inside the specified carrier range, then a local numerical search refines its frequency. A stationary harmonic fit checks the candidate. Near-boundary peaks and residuals above 5% of fundamental RMS require review. Silence and invalid windows are reported individually; gaps are never interpolated. A summary is provided only when every window passes. It separates mean pitch offset from RMS windowed frequency deviation around that mean, both relative to the nominal frequency.

This is a preliminary carrier tracker, not a standardized wow/flutter meter. Window averaging smooths rapid modulation; no modulation bandwidth, DIN/IEC weighting or detector is implemented. Noise, neighboring tones and fast modulation can bias or invalidate estimates. The method cannot distinguish tape speed error from recording/playback clock error. Passing these heuristic checks is not proof of measurement accuracy on physical tape. Do not interpret its windowed RMS statistic as a standardized wow/flutter percentage.

Synthetic tests cover a 3163.27 Hz carrier with noise/DC/harmonics, a known 4 Hz/s drift, 3 Hz peak modulation at 0.5 Hz, dropouts, unrelated noise, search boundaries, invalid inputs and unchanged WAV bytes. Fixture tolerances are 0.005 Hz for stationary frequency, 0.01 Hz for the drift trajectory and 0.02 Hz for slow modulation; they are not guaranteed hardware accuracy specifications.

## Unweighted noise spectrum

```sh
python3 tools/analyze_noise.py recorded-silence.wav --start 3 --duration 10 --segment-samples 8192 --low-hz 20 --high-hz 20000
```

Select a stationary noise-only portion using the actual recording notes. The tool cannot determine whether a signal is tape hiss, interface noise, hum or intentional audio. It uses the shared mono PCM reader and optional NumPy dependency, preserves original bytes and records the checksum and segment start time.

The report includes global DC offset, AC RMS over the complete selected segment, and a one-sided Welch power spectral density using symmetric Hann windows with 50% overlap. Only the global mean is removed; each window is not individually detrended. PSD units are full-scale amplitude squared per Hz. Band RMS is the square root of the sum of selected PSD bins times bin spacing. Requested edges include complete bins whose centers fall inside the band; included centers, bin spacing and window equivalent noise bandwidth are reported. This is not an exact brick-wall filter. Incomplete trailing windows are excluded from PSD, with the tail count reported; full-segment AC RMS still includes them.

The level convention is 0 dBFS for RMS amplitude 1, so a full-scale sine is -3.0103 dBFS RMS. Digital silence returns zero power and null logarithmic levels. There is no A-weighting, absolute voltage calibration, automatic hum removal or noise-source attribution. Hum and tones contribute to band power. Successful calculation does not establish that the selected take is suitable for physical calibration. Use the intake clipping/routing checks and session notes first.

Synthetic checks cover seeded white-noise RMS/density/bandwidth, a known moving-average filter spectrum, 60 Hz hum with DC offset, Parseval normalization including Nyquist, silence, invalid inputs, tail accounting and unchanged WAV files. These establish numerical behavior only, not the recorder's actual noise profile.
