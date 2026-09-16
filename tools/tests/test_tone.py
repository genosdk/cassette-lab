from pathlib import Path
import sys
import tempfile
import unittest
import wave
import numpy as np
sys.path.insert(0,str(Path(__file__).parents[1]))
from analyze_tone import measure,compare,analyze


class ToneTests(unittest.TestCase):
    def test_noninteger_cycles_phase_dc_and_known_harmonics(self):
        rate,f=48000,997.3
        t=np.arange(10007)/rate
        x=.03+.2*np.sin(2*np.pi*f*t+.7)+.01*np.cos(4*np.pi*f*t+.3)+.004*np.sin(6*np.pi*f*t-1)
        r=measure(x,rate,f)
        self.assertTrue(r['accepted'])
        self.assertAlmostEqual(r['dc_offset'],.03,places=10)
        self.assertAlmostEqual(r['fundamental_peak'],.2,places=10)
        self.assertAlmostEqual(r['thd_ratio'],np.hypot(.01,.004)/.2,places=10)
        self.assertLess(r['residual_rms'],1e-12)

    def test_cubic_distortion_against_analytic_identity(self):
        rate,f,a,k=48000,1000,.3,.8
        x=a*np.sin(2*np.pi*f*np.arange(9600)/rate)
        r=measure(x+k*x**3,rate,f)
        fundamental=a+3*k*a**3/4
        third=k*a**3/4
        self.assertAlmostEqual(r['fundamental_peak'],fundamental,places=10)
        self.assertAlmostEqual(r['harmonics'][2]['peak_amplitude'],third,places=10)
        self.assertAlmostEqual(r['thd_ratio'],third/fundamental,places=10)

    def test_discrete_response_of_known_fir(self):
        rate=48000
        # y[n] = 0.6*x[n] + 0.2*x[n-1], evaluated in steady state.
        for f in (100,1000,10000):
            n=np.arange(12000)
            x=.2*np.sin(2*np.pi*f*n/rate)
            y=.6*x+.2*.2*np.sin(2*np.pi*f*(n-1)/rate)
            r=compare(x,y,rate,f)
            expected=20*np.log10(abs(.6+.2*np.exp(-2j*np.pi*f/rate)))
            self.assertTrue(r['accepted'])
            self.assertAlmostEqual(r['fundamental_gain_db'],expected,places=9)

    def test_noise_and_wrong_frequency_are_not_silent_successes(self):
        rng=np.random.default_rng(4)
        t=np.arange(12000)/48000
        x=.2*np.sin(2*np.pi*1000*t)
        r=measure(x+rng.normal(0,.001,len(t)),48000,1000)
        self.assertTrue(r['accepted'])
        self.assertAlmostEqual(r['residual_rms'],.001,delta=.00003)
        r=compare(x,.2*np.sin(2*np.pi*1002*t),48000,1000)
        self.assertFalse(r['accepted'])
        self.assertIsNone(r['fundamental_gain_db'])

    def test_nyquist_omissions_and_invalid_inputs(self):
        x=.2*np.sin(2*np.pi*10000*np.arange(1000)/48000)
        r=measure(x,48000,10000)
        self.assertEqual(r['omitted_orders_at_or_above_nyquist'],[3,4,5])
        r=measure(x,48000,10000,harmonics=1)
        self.assertIsNone(r['thd_ratio'])
        for bad in (np.zeros(1000),np.ones(1000),np.full(1000,np.nan),np.zeros(10)):
            with self.assertRaises(ValueError):measure(bad,48000,1000)
        for f in (0,24000,float('nan')):
            with self.assertRaises(ValueError):measure(x,48000,f)

    def test_wav_segment_and_hash_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'tone.wav'
            x=np.r_[np.zeros(4800),.2*np.sin(2*np.pi*1000*np.arange(4800)/48000),np.zeros(4800)]
            data=np.rint(x*32768).astype('<i2').tobytes()
            with wave.open(str(p),'wb') as w:
                w.setparams((1,2,48000,0,'NONE','not compressed'));w.writeframes(data)
            before=p.read_bytes()
            r=analyze(p,1000,.1,.1,reference=p,reference_start=.1)
            self.assertTrue(r['accepted'])
            self.assertAlmostEqual(r['fundamental_gain_db'],0,places=12)
            self.assertEqual(r['capture_sha256'],r['reference_sha256'])
            self.assertEqual(before,p.read_bytes())
            with self.assertRaises(ValueError):analyze(p,1000,.2,.2)


if __name__=='__main__':unittest.main()
