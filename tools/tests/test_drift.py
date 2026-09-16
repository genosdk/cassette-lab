from pathlib import Path
import sys
import tempfile
import unittest
import wave
import numpy as np
sys.path.insert(0,str(Path(__file__).parents[1]))
from analyze_drift import frequency,track,analyze


class DriftTests(unittest.TestCase):
    def test_constant_offset_with_noise_dc_harmonics(self):
        rate=48000;t=np.arange(4800)/rate;f=3163.27
        x=.03+.2*np.sin(2*np.pi*f*t+.4)+.01*np.sin(4*np.pi*f*t)
        x+=np.random.default_rng(8).normal(0,.0002,len(t))
        r=frequency(x,rate,3150,100)
        self.assertTrue(r['accepted'],r)
        self.assertAlmostEqual(r['frequency_hz'],f,delta=.005)

    def test_linear_drift(self):
        rate=48000;t=np.arange(rate)/rate
        x=.2*np.sin(2*np.pi*(3147*t+2*t*t))
        r=track(x,rate)
        self.assertTrue(r['accepted'],r)
        for row in r['windows']:
            self.assertAlmostEqual(row['frequency_hz'],3147+4*row['center_seconds'],delta=.01)
        self.assertAlmostEqual(r['summary']['mean_frequency_hz'],3149,delta=.01)

    def test_slow_modulation(self):
        rate=48000;t=np.arange(rate*2)/rate
        # Instantaneous frequency = 3150 + 3*sin(2*pi*0.5*t).
        phase=2*np.pi*3150*t-6*np.cos(np.pi*t)
        r=track(.2*np.sin(phase),rate)
        self.assertTrue(r['accepted'],r)
        for row in r['windows']:
            expected=3150+3*np.sin(np.pi*row['center_seconds'])
            self.assertAlmostEqual(row['frequency_hz'],expected,delta=.02)

    def test_dropout_noise_and_search_boundary(self):
        rate=48000;t=np.arange(24000)/rate
        x=.2*np.sin(2*np.pi*3150*t);x[9600:14400]=0
        r=track(x,rate)
        self.assertFalse(r['accepted']);self.assertIsNone(r['summary'])
        self.assertLess(r['valid_windows'],r['total_windows'])
        noise=np.random.default_rng(7).uniform(-.2,.2,4800)
        self.assertFalse(frequency(noise,rate,3150,100)['accepted'])
        boundary=.2*np.sin(2*np.pi*3250*np.arange(4800)/rate)
        self.assertFalse(frequency(boundary,rate,3150,100)['accepted'])

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):track(np.zeros(12),48000)
        with self.assertRaises(ValueError):track(np.zeros(4800),48000,hop_seconds=.2)
        with self.assertRaises(ValueError):frequency(np.zeros(4800),48000,3150,100)
        with self.assertRaises(ValueError):track(np.ones(4800)*np.nan,48000)

    def test_file_unchanged_and_segment_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'tone.wav';rate=48000;t=np.arange(14400)/rate
            x=.2*np.sin(2*np.pi*3157*t)
            with wave.open(str(path),'wb') as w:
                w.setparams((1,2,rate,0,'NONE','not compressed'))
                w.writeframes(np.rint(x*32768).astype('<i2').tobytes())
            before=path.read_bytes()
            r=analyze(path,.05,.2)
            self.assertTrue(r['accepted'])
            self.assertAlmostEqual(r['summary']['mean_frequency_hz'],3157,delta=.005)
            self.assertEqual(r['segment_start_seconds'],.05)
            self.assertEqual(path.read_bytes(),before)


if __name__=='__main__':unittest.main()
