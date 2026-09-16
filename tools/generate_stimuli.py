#!/usr/bin/env python3
"""Deterministic mono 24-bit PCM measurement signals; standard library only."""
import argparse
import hashlib
import json
import math
import wave
from pathlib import Path

SAMPLE_RATES = (48000, 96000, 192000)


def specifications():
    specs = [('reference_1000_m18', 10, -18, 1000, 1000),
             ('speed_3150_m18', 60, -18, 3150, 3150),
             ('silence', 60, None, 0, 0)]
    specs += [(f'sweep_m{-db}', 20, db, 30, 20000) for db in (-30, -18, -6)]
    specs += [(f'sine{hz}_m{-db}', 10, db, hz, hz)
              for hz in (100, 1000, 10000) for db in (-30, -18, -12, -6)]
    return specs


def write_signal(path, sr, spec):
    name, duration, db, f0, f1 = spec
    peak = 0
    nactive, pad = int(sr * duration), sr * 2
    amp = 0 if db is None else 10 ** (db / 20)
    # Exclusive creation also protects against files appearing after preflight.
    with path.open('xb') as target, wave.open(target, 'wb') as w:
        w.setparams((1, 3, sr, 0, 'NONE', 'not compressed'))
        w.writeframesraw(bytes(pad * 3))
        chunk = bytearray()
        for n in range(nactive):
            t = n / sr
            phase = (2 * math.pi * f0 * t if f0 == f1 else
                     2 * math.pi * f0 * duration / math.log(f1 / f0)
                     * math.expm1(t / duration * math.log(f1 / f0)))
            fade = min(1.0, n / (sr * .01), (nactive - 1 - n) / (sr * .01))
            value = round(amp * fade * math.sin(phase) * 8388607)
            peak = max(peak, abs(value))
            chunk.extend(value.to_bytes(3, 'little', signed=True))
            if len(chunk) >= 24576:
                w.writeframesraw(chunk)
                chunk.clear()
        w.writeframesraw(chunk)
        w.writeframesraw(bytes(pad * 3))
    with path.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    return dict(file=path.name, sample_rate=sr, channels=1, bits=24,
                active_seconds=duration, padding_seconds_each=2, peak_dbfs=db,
                measured_peak=peak / 8388607, sha256=digest)


def generate(out, sr):
    if sr not in SAMPLE_RATES:
        raise ValueError(f'Sample rate must be one of {SAMPLE_RATES}')
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise FileExistsError('Output must be a new or empty directory; existing files are never overwritten')
    out.mkdir(parents=True, exist_ok=True)
    manifest = [write_signal(out / (spec[0] + '.wav'), sr, spec) for spec in specifications()]
    with (out / 'manifest.json').open('x') as target:
        target.write(json.dumps(manifest, indent=2) + '\n')
    print(f'Generated {len(manifest)} files at {sr} Hz in {out}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('measurements/stimuli'))
    parser.add_argument('--sample-rate', type=int, choices=SAMPLE_RATES, default=96000)
    args = parser.parse_args()
    try:
        generate(args.out, args.sample_rate)
    except (OSError, ValueError) as exc:
        parser.exit(1, f'Generation failed: {exc}\n')
