#!/usr/bin/env python3
"""Read-only unweighted noise/power spectrum; no source attribution."""
import argparse
import json
from pathlib import Path
import wave
import numpy as np
from analyze_tone import section


def spectrum(samples, rate, segment_samples=8192, low_hz=20., high_hz=20000.):
    x=np.asarray(samples,dtype=np.float64)
    if x.ndim!=1 or not np.isfinite(x).all() or len(x)==0:
        raise ValueError('Expected nonempty finite mono audio')
    if not np.isfinite(rate) or rate<=0 or not all(np.isfinite(v) for v in (low_hz,high_hz)) or not 0<=low_hz<high_hz<=rate/2:
        raise ValueError('Band must lie between zero and Nyquist')
    if type(segment_samples) is not int or segment_samples<64 or segment_samples%2 or len(x)<segment_samples:
        raise ValueError('Segment size must be an even integer >=64 fitting the audio')
    if np.max(np.abs(x))>=1:
        raise ValueError('Full-scale/overrange samples; review clipping')
    dc=float(x.mean());centered=x-dc
    n=segment_samples;hop=n//2
    window=np.hanning(n)
    psd=np.zeros(n//2+1)
    starts=range(0,len(x)-n+1,hop)
    for start in starts:
        transform=np.fft.rfft(centered[start:start+n]*window)
        power=np.abs(transform)**2/(rate*np.dot(window,window))
        power[1:-1]*=2
        psd+=power
    psd/=len(starts)
    freq=np.fft.rfftfreq(n,1/rate);df=rate/n
    selected=(freq>=low_hz)&(freq<=high_hz)
    if not np.any(selected):raise ValueError('No FFT bin centers inside requested band')
    rms=float(np.sqrt(np.mean(centered**2)))
    band_rms=float(np.sqrt(psd[selected].sum()*df))
    def db(value):return float(20*np.log10(value)) if value>0 else None
    return {'accepted':True,'sample_rate':rate,'samples':len(x),'dc_offset':dc,
            'ac_rms':rms,'ac_rms_dbfs':db(rms),'band_rms':band_rms,'band_rms_dbfs':db(band_rms),
            'requested_band_hz':[low_hz,high_hz],
            'included_bin_centers_hz':[float(freq[selected][0]),float(freq[selected][-1])],
            'segment_samples':n,'segments':len(starts),'hop_samples':hop,'bin_spacing_hz':df,
            'window_enbw_hz':float(rate*np.dot(window,window)/window.sum()**2),
            'unprocessed_tail_samples':len(x)-(starts[-1]+n),
            'frequency_hz':freq.tolist(),'power_density_fs2_per_hz':psd.tolist(),
            'method':'One-sided Welch PSD; symmetric Hann; 50% overlap; global DC removal; sum selected bins times bin spacing',
            'level_reference':'0 dBFS RMS means RMS amplitude 1; full-scale sine RMS is -3.0103 dBFS',
            'limitations':'Unweighted total AC power includes hum and tones; not isolated tape hiss, dBu, A-weighted noise or standardized SNR. Band edges select whole bins; spectral leakage remains.'}


def analyze(path,start,duration,segment_samples=8192,low_hz=20.,high_hz=20000.):
    x,rate,digest=section(path,start,duration)
    result=spectrum(x,rate,segment_samples,low_hz,high_hz)
    result.update(capture_sha256=digest,segment_start_seconds=start)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('capture',type=Path)
    p.add_argument('--start',type=float,required=True)
    p.add_argument('--duration',type=float,required=True)
    p.add_argument('--segment-samples',type=int,default=8192)
    p.add_argument('--low-hz',type=float,default=20.)
    p.add_argument('--high-hz',type=float,default=20000.)
    a=p.parse_args()
    try:report=analyze(a.capture,a.start,a.duration,a.segment_samples,a.low_hz,a.high_hz)
    except (OSError,ValueError,EOFError,wave.Error) as exc:p.exit(1,f'Analysis failed: {exc}\n')
    print(json.dumps(report,indent=2,allow_nan=False))
