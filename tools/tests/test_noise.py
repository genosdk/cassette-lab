from pathlib import Path
import sys
import tempfile
import unittest
import wave
import numpy as np
sys.path.insert(0,str(Path(__file__).parents[1]))
from analyze_noise import spectrum,analyze


class NoiseTests(unittest.TestCase):
    def test_white_noise_density_rms_and_bandwidth(self):
        rate=48000;sigma=.01
        x=np.random.default_rng(18).normal(0,sigma,rate*8)
        r=spectrum(x,rate,4096,3000,9000)
        self.assertAlmostEqual(r['ac_rms'],sigma,delta=.00005)
        f=np.array(r['frequency_hz']);p=np.array(r['power_density_fs2_per_hz'])
        mask=(f>=3000)&(f<=9000)
        self.assertAlmostEqual(p[mask].mean(),2*sigma**2/rate,delta=2*sigma**2/rate*.025)
        expected=sigma*np.sqrt(mask.sum()*r['bin_spacing_hz']/(rate/2))
        self.assertAlmostEqual(r['band_rms'],expected,delta=expected*.02)

    def test_filtered_noise_known_transfer(self):
        rate=48000
        x=np.random.default_rng(3).normal(0,.01,rate*8)
        y=(x[1:]+x[:-1])/2
        r=spectrum(y,rate,4096,0,24000)
        f=np.array(r['frequency_hz']);p=np.array(r['power_density_fs2_per_hz'])
        # Moving-average filter power gain is cos(pi*f/fs)^2.
        expected=2*.01**2/rate*np.cos(np.pi*f/rate)**2
        for low,high in ((1000,5000),(12000,18000)):
            mask=(f>=low)&(f<=high)
            self.assertAlmostEqual(p[mask].sum()/expected[mask].sum(),1,delta=.04)
        self.assertAlmostEqual(r['ac_rms'],.01/np.sqrt(2),delta=.00006)

    def test_hum_level_and_dc_exclusion(self):
        rate=48000;t=np.arange(rate*2)/rate
        x=.03+.01*np.sin(2*np.pi*60*t)
        r=spectrum(x,rate,48000,40,80)
        self.assertAlmostEqual(r['dc_offset'],.03,places=10)
        self.assertAlmostEqual(r['band_rms'],.01/np.sqrt(2),delta=1e-7)
        peak=int(np.argmax(r['power_density_fs2_per_hz']))
        self.assertEqual(r['frequency_hz'][peak],60)
        self.assertAlmostEqual(r['band_rms_dbfs'],20*np.log10(.01/np.sqrt(2)),places=5)

    def test_parseval_normalization_and_nyquist(self):
        rate=48000;n=1024
        x=np.random.default_rng(9).uniform(-.1,.1,n)
        r=spectrum(x,rate,n,0,rate/2)
        w=np.hanning(n)
        expected=np.sum(((x-x.mean())*w)**2)/np.sum(w*w)
        self.assertAlmostEqual(r['band_rms']**2,expected,places=14)
        nyquist=.1*(-1.)**np.arange(n)
        r=spectrum(nyquist,rate,n,0,rate/2)
        self.assertAlmostEqual(r['band_rms'],.1,places=10)

    def test_silence_invalid_and_tail(self):
        r=spectrum(np.zeros(2100),48000,1024)
        self.assertEqual(r['ac_rms'],0);self.assertIsNone(r['band_rms_dbfs'])
        self.assertEqual(r['unprocessed_tail_samples'],52)
        for x in (np.ones(1024),np.full(1024,np.nan),np.zeros(10)):
            with self.assertRaises(ValueError):spectrum(x,48000,1024)
        with self.assertRaises(ValueError):spectrum(np.zeros(1024),48000,1023)
        with self.assertRaises(ValueError):spectrum(np.zeros(1024),48000,1024,0,25000)

    def test_file_bytes_and_checksum(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'noise.wav'
            x=np.random.default_rng(1).normal(0,.01,4800)
            with wave.open(str(path),'wb') as w:
                w.setparams((1,2,48000,0,'NONE','not compressed'))
                w.writeframes(np.rint(x*32768).astype('<i2').tobytes())
            before=path.read_bytes()
            r=analyze(path,0,.1,1024)
            self.assertTrue(r['accepted']);self.assertEqual(len(r['capture_sha256']),64)
            self.assertEqual(path.read_bytes(),before)


if __name__=='__main__':unittest.main()
