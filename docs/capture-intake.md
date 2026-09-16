# Returned measurement intake

The partner's Ableton recording instructions are unchanged. This tool is for us after receiving their files; the partner does not need Python or GitHub.

Keep the original returned folder intact. With Python 3.11 or newer, run from the repository root:

```sh
python tools/check_captures.py /path/to/returned-recordings > capture-report.json
```

The tool scans WAV files recursively, computes SHA-256 checksums and reports duration, format, sample rate, channels, per-channel peak/RMS/DC offset, full-scale sample counts, nonfinite samples and byte-identical duplicates. It does not modify, normalize, resample or rename audio. PCM 16/24/32-bit and IEEE float 32-bit RIFF WAV are supported, including matching extensible subtypes. RF64, compressed audio and other formats produce explicit errors. Exit code 1 means unreadable/unsupported files or no WAV files; warnings remain review items and do not change the exit code.

Review warnings in context: intentional silence is valid, stereo needs a routing check, and full-scale samples suggest possible digital clipping rather than proving analog tape clipping. Floating-point values above unity are reported, not discarded. RMS/DC include the entire file and silence padding; files with nonfinite samples are unsuitable for calibration. A null peak_dbfs means digital silence. Duplicate checking compares complete file bytes, not just audio samples.

Compare the inventory with the partner's completed checklist and session notes. This tool does not establish session completeness, correct routing, tape playback provenance, or correct stimulus identity. Preserve loopbacks, recorder returns, level settings and dry music references separately. Resolve missing takes and routing issues before fitting a model. Alignment, frequency response, distortion and wow/flutter analysis are the next gate once actual captures are available.

## Logic host checks still needed

The user confirmed AU loading as an effect on 2026-09-16. At Input 0 dB, Output 0 dB and Mix 100%, the current scaffold should sound transparent. Compare bypass at matched level. Then automate Input/Output/Mix, save and reopen a project with nondefault settings, try mono and stereo instances, and compare realtime playback with an offline bounce. Record Logic/macOS versions, sample rate, buffer size and any differences. Successful loading alone does not establish these results.
