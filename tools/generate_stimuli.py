#!/usr/bin/env python3
"""Deterministic mono 24-bit PCM measurement signals; standard library only."""
import argparse, hashlib, json, math, wave
from pathlib import Path

def generate(out, sr):
    out.mkdir(parents=True, exist_ok=True)
    specs=[('reference_1000_m18',10,-18,1000,1000),
           ('speed_3150_m18',60,-18,3150,3150),('silence',60,None,0,0)]
    specs += [(f'sweep_m{-db}',20,db,30,20000) for db in (-30,-18,-6)]
    specs += [(f'sine{hz}_m{-db}',10,db,hz,hz) for hz in (100,1000,10000) for db in (-30,-18,-12,-6)]
    manifest=[]
    for name,duration,db,f0,f1 in specs:
        path=out/(name+'.wav'); peak=0; nactive=int(sr*duration); pad=sr*2
        amp=0 if db is None else 10**(db/20)
        with wave.open(str(path),'wb') as w:
            w.setparams((1,3,sr,0,'NONE','not compressed'))
            w.writeframesraw(bytes(pad*3))
            chunk=bytearray()
            for n in range(nactive):
                t=n/sr
                phase=(2*math.pi*f0*t if f0==f1 else
                       2*math.pi*f0*duration/math.log(f1/f0)*math.expm1(t/duration*math.log(f1/f0)))
                fade=min(1.0,n/(sr*.01),(nactive-1-n)/(sr*.01))
                value=round(amp*fade*math.sin(phase)*8388607)
                peak=max(peak,abs(value)); chunk.extend(value.to_bytes(3,'little',signed=True))
                if len(chunk)>=24576: w.writeframesraw(chunk); chunk.clear()
            w.writeframesraw(chunk); w.writeframesraw(bytes(pad*3))
        manifest.append(dict(file=path.name,sample_rate=sr,channels=1,bits=24,active_seconds=duration,
            padding_seconds_each=2,peak_dbfs=db,measured_peak=peak/8388607,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Generated {len(manifest)} files at {sr} Hz in {out}')
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--out',type=Path,default=Path('measurements/stimuli'))
    p.add_argument('--sample-rate',type=int,choices=[48000,96000,192000],default=96000)
    args=p.parse_args(); generate(args.out,args.sample_rate)
