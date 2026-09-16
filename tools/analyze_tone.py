#!/usr/bin/env python3
"""Read-only stationary-tone harmonic analysis and discrete response comparison."""
import argparse
import json
from pathlib import Path
import wave
import numpy as np
from analyze_alignment import read_mono


def measure(samples, rate, frequency, harmonics=5):
    x = np.asarray(samples, dtype=np.float64)
    if x.ndim != 1 or len(x) < 64 or not np.isfinite(x).all():
        raise ValueError('Provide at least 64 finite mono samples')
    if not np.isfinite(rate) or not np.isfinite(frequency) or not 0 < frequency < rate/2:
        raise ValueError('Frequency must be positive and below Nyquist at a finite sample rate')
    if type(harmonics) is not int or not 1 <= harmonics <= 20:
        raise ValueError('Harmonic count must be an integer from 1 through 20')
    if len(x)*frequency/rate < 20:
        raise ValueError('Select at least 20 fundamental cycles')
    if np.max(np.abs(x)) >= 1:
        raise ValueError('Full-scale/overrange samples; review clipping')
    orders = [h for h in range(1, harmonics+1) if h*frequency < rate/2]
    phase = 2*np.pi*frequency*np.arange(len(x))/rate
    columns = [np.ones(len(x))]
    for h in orders:
        columns.extend([np.cos(h*phase), np.sin(h*phase)])
    design = np.column_stack(columns)
    coeff, _, rank, singular = np.linalg.lstsq(design, x, rcond=None)
    if rank != len(columns) or singular[0]/singular[-1] > 1e8:
        raise ValueError('Ill-conditioned harmonic fit')
    amplitudes = np.hypot(coeff[1::2], coeff[2::2])
    fundamental = float(amplitudes[0])
    if fundamental < 1e-9:
        raise ValueError('No measurable fundamental at the supplied frequency')
    residual = float(np.sqrt(np.mean((x-design@coeff)**2)))
    relative_residual = residual/(fundamental/np.sqrt(2))
    warnings = []
    if relative_residual > .05:
        warnings.append('Residual exceeds 5% of fundamental RMS; check frequency, drift, noise or nonstationarity')
    rows = [{'order':h, 'frequency_hz':h*frequency, 'peak_amplitude':float(a),
             'level_dbc':float(20*np.log10(a/fundamental)) if a > 0 else None}
            for h,a in zip(orders,amplitudes)]
    return {'accepted':not warnings, 'frequency_hz':frequency, 'sample_rate':rate,
            'samples':len(x), 'duration_seconds':len(x)/rate, 'dc_offset':float(coeff[0]),
            'fundamental_peak':fundamental, 'harmonics':rows,
            'requested_harmonics':harmonics, 'omitted_orders_at_or_above_nyquist':list(range(len(orders)+1,harmonics+1)),
            'thd_ratio':float(np.linalg.norm(amplitudes[1:])/fundamental) if len(orders)>1 else None,
            'residual_rms':residual, 'residual_to_fundamental_rms':relative_residual,
            'warnings':warnings,
            'method':'Simultaneous unweighted least-squares DC/sine/cosine fit at supplied stationary frequency',
            'limitations':'Partial THD over reported harmonics only; residual is not standardized THD+N or tape noise; no frequency/drift estimation'}


def compare(reference, returned, rate, frequency, harmonics=5):
    ref = measure(reference, rate, frequency, harmonics)
    out = measure(returned, rate, frequency, harmonics)
    accepted = ref['accepted'] and out['accepted']
    return {'accepted':accepted, 'reference':ref, 'return':out,
            'fundamental_gain_db':float(20*np.log10(out['fundamental_peak']/ref['fundamental_peak'])) if accepted else None,
            'limitations':'One stationary response point; does not subtract interface distortion or identify tape-only distortion'}


def section(path, start, duration):
    if not np.isfinite(start) or start < 0 or not np.isfinite(duration) or duration <= 0:
        raise ValueError('Start must be nonnegative and duration positive, both finite')
    samples, rate, digest = read_mono(path)
    first, count = int(round(start*rate)), int(round(duration*rate))
    if count < 1 or first+count > len(samples):
        raise ValueError('Requested analysis segment exceeds file or is empty')
    return samples[first:first+count], rate, digest


def analyze(path, frequency, start, duration, reference=None, reference_start=0., harmonics=5):
    samples, rate, digest = section(path, start, duration)
    if reference is None:
        report = measure(samples,rate,frequency,harmonics)
    else:
        ref, ref_rate, ref_hash = section(reference,reference_start,duration)
        if ref_rate != rate:
            raise ValueError('Sample rates differ; originals will not be resampled')
        report = compare(ref,samples,rate,frequency,harmonics)
        report.update(reference_sha256=ref_hash,reference_start_seconds=reference_start)
    report.update(capture_sha256=digest,capture_start_seconds=start,requested_duration_seconds=duration)
    return report


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('capture',type=Path)
    p.add_argument('--frequency',type=float,required=True)
    p.add_argument('--start',type=float,required=True)
    p.add_argument('--duration',type=float,required=True)
    p.add_argument('--harmonics',type=int,default=5)
    p.add_argument('--reference',type=Path)
    p.add_argument('--reference-start',type=float,default=0.)
    args=p.parse_args()
    try:
        result=analyze(args.capture,args.frequency,args.start,args.duration,args.reference,args.reference_start,args.harmonics)
    except (OSError, ValueError, EOFError, wave.Error) as exc:
        p.exit(1,f'Analysis failed: {exc}\n')
    print(json.dumps(result,indent=2,allow_nan=False))
    raise SystemExit(0 if result['accepted'] else 2)
