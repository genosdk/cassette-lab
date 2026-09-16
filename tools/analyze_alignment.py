#!/usr/bin/env python3
"""Read-only integer-delay analysis of mono PCM WAV pairs; no resampling."""
import argparse
import hashlib
import json
from pathlib import Path
import wave
import numpy as np


def read_mono(path):
    with path.open('rb') as source:
        digest = hashlib.file_digest(source, 'sha256').hexdigest()
    with wave.open(str(path), 'rb') as audio:
        channels, width, rate, frames = (audio.getnchannels(), audio.getsampwidth(),
                                         audio.getframerate(), audio.getnframes())
        if channels != 1 or width not in (2, 3, 4) or audio.getcomptype() != 'NONE':
            raise ValueError('Alignment currently requires mono PCM 16/24/32-bit WAV')
        data = audio.readframes(frames)
        if len(data) != frames * width:
            raise ValueError('Truncated audio')
    if width == 3:
        raw = np.frombuffer(data, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        values = raw[:, 0] | (raw[:, 1] << 8) | (raw[:, 2] << 16)
        values = (values ^ 0x800000) - 0x800000
    else:
        values = np.frombuffer(data, dtype='<i2' if width == 2 else '<i4')
    return values.astype(np.float64) / (2 ** (width * 8 - 1)), rate, digest


def estimate(source, capture, rate, max_delay_seconds=2.0):
    x, y = np.asarray(source, dtype=np.float64), np.asarray(capture, dtype=np.float64)
    if x.ndim != 1 or y.ndim != 1 or min(len(x), len(y)) < 64:
        raise ValueError('Provide mono arrays with at least 64 samples each')
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('Nonfinite audio samples')
    if not np.isfinite(rate) or rate <= 0 or not np.isfinite(max_delay_seconds) or max_delay_seconds <= 0:
        raise ValueError('Sample rate and delay bound must be finite and positive')
    if max(np.max(np.abs(x)), np.max(np.abs(y))) >= 1:
        raise ValueError('Full-scale/overrange audio: review clipping before alignment')
    bound = int(round(rate * max_delay_seconds))
    if bound < 1:
        raise ValueError('Delay bound must cover at least one sample')
    # corr[k] = sum x[n] * y[n+k]. Positive delay means capture is late.
    fft_size = 1 << (len(x) + len(y) - 2).bit_length()
    cross = np.fft.irfft(np.conj(np.fft.rfft(x, fft_size)) * np.fft.rfft(y, fft_size), fft_size)
    lags = np.arange(max(-bound, 1-len(x)), min(bound, len(y)-1) + 1)
    xa = np.maximum(0, -lags)
    ya = np.maximum(0, lags)
    count = np.minimum(len(x)-xa, len(y)-ya)
    valid = count >= max(64, int(np.ceil(min(len(x), len(y)) * .5)))
    def sums(a, start):
        c = np.r_[0., np.cumsum(a)]
        c2 = np.r_[0., np.cumsum(a*a)]
        return c[start+count]-c[start], c2[start+count]-c2[start]
    sx, qx = sums(x, xa)
    sy, qy = sums(y, ya)
    vx, vy = np.maximum(0, qx-sx*sx/count), np.maximum(0, qy-sy*sy/count)
    denom = np.sqrt(vx*vy)
    valid &= denom > 1e-15
    if not np.any(valid):
        raise ValueError('Insufficient nonconstant overlapping audio')
    scores = np.zeros(len(lags))
    scores[valid] = (cross[lags[valid] % fft_size] - sx[valid]*sy[valid]/count[valid]) / denom[valid]
    scores = np.clip(scores, -1., 1.)
    index = int(np.argmax(np.where(valid, np.abs(scores), -1)))
    delay, corr = int(lags[index]), float(scores[index])
    # Exclude the immediate correlation lobe; periodic audio remains ambiguous.
    outside = valid & (np.abs(lags-delay) > max(1, int(rate * .001)))
    alternate = float(np.max(np.abs(scores[outside]))) if np.any(outside) else None
    warnings = []
    if abs(corr) < .8: warnings.append('Low correlation; delay candidate is unreliable')
    if alternate is not None and alternate >= .95 * abs(corr):
        warnings.append('Ambiguous correlation peaks; use a broadband signal or a tighter justified search range')
    if abs(delay) == bound: warnings.append('Peak reaches search boundary; increase delay bound')
    a, b, n = int(xa[index]), int(ya[index]), int(count[index])
    xx, yy = x[a:a+n], y[b:b+n]
    gain = float(np.dot(xx-xx.mean(), yy-yy.mean()) / np.dot(xx-xx.mean(), xx-xx.mean()))
    return {'accepted': not warnings, 'delay_samples': delay, 'delay_seconds': delay/rate,
            'correlation': corr, 'alternate_peak_abs_correlation': alternate,
            'polarity': 'inverted' if corr < 0 else 'normal', 'overlap_samples': n,
            'relative_gain_linear': gain if not warnings else None,
            'warnings': warnings,
            'method': 'overlap-normalized zero-mean FFT correlation; integer samples; 50% minimum overlap',
            'limitations': 'Candidate global delay only; no fractional delay, clock-drift correction or tape calibration'}


def analyze(source_path, capture_path, max_delay_seconds=2.0):
    x, rate, source_hash = read_mono(source_path)
    y, capture_rate, capture_hash = read_mono(capture_path)
    if rate != capture_rate:
        raise ValueError('Sample rates differ; original files will not be resampled')
    result = estimate(x, y, rate, max_delay_seconds)
    result.update(sample_rate=rate, source_sha256=source_hash, capture_sha256=capture_hash)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--max-delay', type=float, default=2.0, help='Symmetric search bound in seconds')
    args = parser.parse_args()
    try:
        report = analyze(args.source, args.capture, args.max_delay)
    except (OSError, ValueError, EOFError, wave.Error) as exc:
        parser.exit(1, f'Analysis failed: {exc}\n')
    print(json.dumps(report, indent=2, allow_nan=False))
    raise SystemExit(0 if report['accepted'] else 2)
