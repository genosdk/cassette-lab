#!/usr/bin/env python3
"""Read-only whole-record spectral magnitude ratio for low-level sweep pairs."""
import argparse
import json
from pathlib import Path
import wave
import numpy as np
from analyze_alignment import read_mono


def response(reference, returned, rate, low_hz=30., high_hz=20000., floor_db=-60.):
    arrays = [np.asarray(a, dtype=np.float64) for a in (reference, returned)]
    for a in arrays:
        if a.ndim != 1 or len(a) < 64 or not np.isfinite(a).all():
            raise ValueError('Expected at least 64 finite mono samples per record')
        if np.max(np.abs(a)) >= 1:
            raise ValueError('Full-scale/overrange samples; review clipping')
    if not all(np.isfinite(v) for v in (rate, low_hz, high_hz, floor_db)):
        raise ValueError('Parameters must be finite')
    if not 0 < low_hz < high_hz < rate/2 or not -120 <= floor_db < 0:
        raise ValueError('Band must be inside Nyquist; floor must be in [-120, 0) dB')
    # A common transform length preserves the convolution magnitude relation.
    # No taper: the complete excitation and response tail must be included.
    n = max(map(len, arrays))
    x, y = [np.abs(np.fft.rfft(a, n=n)) for a in arrays]
    f = np.fft.rfftfreq(n, 1/rate)
    band = (f >= low_hz) & (f <= high_hz)
    if not band.any() or x.max() == 0:
        raise ValueError('No reference excitation or no bins in requested band')
    valid = x[band] >= x.max()*10**(floor_db/20)
    gain = [float(20*np.log10(b/a)) if ok and b > 0 else None
            for a, b, ok in zip(x[band], y[band], valid)]
    return {'accepted': bool(valid.all()), 'sample_rate': rate,
            'reference_samples': len(arrays[0]), 'return_samples': len(arrays[1]),
            'fft_samples': n, 'bin_spacing_hz': rate/n,
            'requested_band_hz': [low_hz, high_hz], 'reference_floor_db': floor_db,
            'frequency_hz': f[band].tolist(), 'magnitude_gain_db': gain,
            'reference_excited': valid.tolist(), 'masked_bins': int((~valid).sum()),
            'method': 'Whole-record |FFT(return)| / |FFT(reference)|; common length; zero padding only; no taper or smoothing',
            'limitations': 'Accepted means reference excitation coverage only. Complete sweep and response tail required. Noise, truncation, drift and nonlinearity can bias every bin and are not detected. No coherence, phase, impulse response or calibration claim. Null gain means weak reference or zero return.'}


def analyze(reference, returned, low_hz=30., high_hz=20000., floor_db=-60.):
    x, rate, xhash = read_mono(reference)
    y, other_rate, yhash = read_mono(returned)
    if rate != other_rate:
        raise ValueError('Sample rates must match; no resampling is performed')
    result = response(x, y, rate, low_hz, high_hz, floor_db)
    result.update(reference_sha256=xhash, return_sha256=yhash)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('reference', type=Path)
    p.add_argument('returned', type=Path)
    p.add_argument('--low-hz', type=float, default=30.)
    p.add_argument('--high-hz', type=float, default=20000.)
    p.add_argument('--floor-db', type=float, default=-60.)
    a = p.parse_args()
    try:
        report = analyze(a.reference, a.returned, a.low_hz, a.high_hz, a.floor_db)
    except (OSError, ValueError, EOFError, wave.Error) as exc:
        p.exit(1, f'Analysis failed: {exc}\n')
    print(json.dumps(report, indent=2, allow_nan=False))
    raise SystemExit(0 if report['accepted'] else 2)
