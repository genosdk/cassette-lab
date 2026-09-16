#!/usr/bin/env python3
"""Read-only windowed carrier tracking; not standardized wow/flutter metering."""
import argparse
import json
from pathlib import Path
import wave
import numpy as np
from analyze_tone import measure, section


def frequency(samples, rate, nominal, search_hz):
    x=np.asarray(samples,dtype=np.float64)
    if x.ndim != 1 or len(x)<64 or not np.isfinite(x).all():
        raise ValueError('Provide at least 64 finite mono samples')
    if not all(np.isfinite(v) for v in (rate,nominal,search_hz)) or not 0 < nominal-search_hz < nominal+search_hz < rate/2:
        raise ValueError('Search interval must be positive and below Nyquist')
    if len(x)*(nominal-search_hz)/rate < 20:
        raise ValueError('Window must contain at least 20 cycles at the search lower bound')
    if np.max(np.abs(x))>=1:
        raise ValueError('Full-scale/overrange samples')
    centered=x-x.mean()
    if np.sqrt(np.mean(centered**2))<1e-9:
        raise ValueError('No measurable carrier')
    windowed=centered*np.hanning(len(x))
    size=1 << (8*len(x)-1).bit_length()
    bins=np.fft.rfftfreq(size,1/rate)
    spectrum=np.abs(np.fft.rfft(windowed,size))
    lo,hi=nominal-search_hz,nominal+search_hz
    candidates=np.flatnonzero((bins>=lo)&(bins<=hi))
    if len(candidates)<3:
        raise ValueError('Search interval too narrow for this window')
    peak=int(candidates[np.argmax(spectrum[candidates])])
    spacing=rate/size
    left,right=max(lo,bins[peak]-spacing),min(hi,bins[peak]+spacing)
    time=np.arange(len(x))/rate
    def power(f):
        return abs(np.dot(windowed,np.exp(-2j*np.pi*f*time)))**2
    # Refine the local Hann-window spectral maximum; no audio resampling.
    ratio=(np.sqrt(5)-1)/2
    a,b=right-ratio*(right-left),left+ratio*(right-left)
    pa,pb=power(a),power(b)
    for _ in range(35):
        if pa>pb:
            right,b,pb=b,a,pa
            a=right-ratio*(right-left);pa=power(a)
        else:
            left,a,pa=a,b,pb
            b=left+ratio*(right-left);pb=power(b)
    found=float((left+right)/2)
    fit=measure(x,rate,found,harmonics=3)
    warnings=list(fit['warnings'])
    if min(found-lo,hi-found)<spacing:
        warnings.append('Carrier reaches search boundary')
    return {'accepted':not warnings,'frequency_hz':found,
            'residual_to_fundamental_rms':fit['residual_to_fundamental_rms'],'warnings':warnings}


def track(samples,rate,nominal=3150.,search_hz=100.,window_seconds=.1,hop_seconds=.05):
    x=np.asarray(samples,dtype=np.float64)
    if not all(np.isfinite(v) and v>0 for v in (rate,window_seconds,hop_seconds)):
        raise ValueError('Rate, window and hop must be finite and positive')
    if x.ndim!=1 or not np.isfinite(x).all():
        raise ValueError('Expected finite mono audio')
    if not all(np.isfinite(v) for v in (nominal,search_hz)) or not 0<nominal-search_hz<nominal+search_hz<rate/2:
        raise ValueError('Invalid carrier search interval')
    width,hop=int(round(rate*window_seconds)),int(round(rate*hop_seconds))
    if width<64 or hop<1 or hop>width or len(x)<width:
        raise ValueError('Invalid window/hop or insufficient audio')
    rows=[]
    for start in range(0,len(x)-width+1,hop):
        try:
            row=frequency(x[start:start+width],rate,nominal,search_hz)
        except ValueError as exc:
            row={'accepted':False,'frequency_hz':None,'warnings':[str(exc)]}
        row['center_seconds']=(start+(width-1)/2)/rate
        rows.append(row)
    accepted=all(r['accepted'] for r in rows)
    summary=None
    if accepted:
        values=np.array([r['frequency_hz'] for r in rows])
        mean=float(values.mean())
        summary={'mean_frequency_hz':mean,'mean_offset_percent':100*(mean/nominal-1),
                 'windowed_deviation_rms_percent':float(100*np.sqrt(np.mean((values-mean)**2))/nominal)}
    return {'accepted':accepted,'nominal_hz':nominal,'search_hz':search_hz,
            'window_seconds':width/rate,'hop_seconds':hop/rate,
            'unprocessed_tail_samples':len(x)-(len(rows)-1)*hop-width,
            'valid_windows':sum(r['accepted'] for r in rows),'total_windows':len(rows),
            'summary':summary,'windows':rows,
            'method':'Hann-window spectral peak with local refinement; stationary harmonic residual check',
            'limitations':'Window-averaged carrier estimates; no standardized weighting/detector, flutter bandwidth or clock/tape separation. No correction or resampling.'}


def analyze(path,start,duration,nominal=3150.,search_hz=100.,window_seconds=.1,hop_seconds=.05):
    x,rate,digest=section(path,start,duration)
    report=track(x,rate,nominal,search_hz,window_seconds,hop_seconds)
    report.update(capture_sha256=digest,segment_start_seconds=start,sample_rate=rate)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('capture',type=Path)
    p.add_argument('--start',type=float,required=True)
    p.add_argument('--duration',type=float,required=True)
    p.add_argument('--nominal',type=float,default=3150.)
    p.add_argument('--search-hz',type=float,default=100.)
    p.add_argument('--window',type=float,default=.1)
    p.add_argument('--hop',type=float,default=.05)
    a=p.parse_args()
    try:
        report=analyze(a.capture,a.start,a.duration,a.nominal,a.search_hz,a.window,a.hop)
    except (OSError,ValueError,EOFError,wave.Error) as exc:
        p.exit(1,f'Analysis failed: {exc}\n')
    print(json.dumps(report,indent=2,allow_nan=False))
    raise SystemExit(0 if report['accepted'] else 2)
