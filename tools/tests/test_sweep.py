from pathlib import Path
import sys
import tempfile
import unittest
import wave
import numpy as np
sys.path.insert(0, str(Path(__file__).parents[1]))
from analyze_sweep import response, analyze


class SweepTests(unittest.TestCase):
    def setUp(self):
        self.rate = 48000
        t = np.arange(self.rate)/self.rate
        k = np.log(20000/30)
        self.x = np.pad(.1*np.sin(2*np.pi*30*np.expm1(k*t)/k)*np.hanning(len(t)), (1000, 1000))

    def test_known_fir_and_delay(self):
        h = np.array([.3, .2, .1])
        y = np.pad(np.convolve(self.x, h), (713, 0))
        r = response(self.x, y, self.rate, 100, 15000, -100)
        self.assertTrue(r['accepted'])
        f = np.array(r['frequency_hz'])
        expected = np.abs(sum(v*np.exp(-2j*np.pi*f*i/self.rate) for i,v in enumerate(h)))
        np.testing.assert_allclose(r['magnitude_gain_db'], 20*np.log10(expected), atol=1e-8)

    def test_gain_polarity_and_unequal_padding(self):
        r = response(self.x, np.pad(-.25*self.x, (123, 500)), self.rate, 100, 15000, -100)
        np.testing.assert_allclose(r['magnitude_gain_db'], 20*np.log10(.25), atol=1e-8)

    def test_weak_excitation_mask_and_zero_return(self):
        x = .1*np.cos(2*np.pi*1000*np.arange(48000)/48000)
        r = response(x, x, 48000, 500, 1500)
        self.assertFalse(r['accepted'])
        self.assertGreater(r['masked_bins'], 990)
        self.assertIsNone(r['magnitude_gain_db'][0])
        r = response(self.x, np.zeros_like(self.x), 48000, 100, 15000, -100)
        self.assertTrue(all(v is None for v in r['magnitude_gain_db']))

    def test_small_additive_noise(self):
        y = .5*self.x + np.random.default_rng(5).normal(0, 1e-8, len(self.x))
        r = response(self.x, y, self.rate, 300, 8000)
        self.assertTrue(r['accepted'])
        np.testing.assert_allclose(r['magnitude_gain_db'], 20*np.log10(.5), atol=.002)

    def test_invalid_inputs(self):
        for x in (np.zeros(100), np.ones(100), np.full(100,np.nan), np.zeros((100,2)), np.zeros(3)):
            with self.assertRaises(ValueError): response(x, self.x, self.rate)
        for args in ((0, 20000, -60), (30, 24000, -60), (30, 20000, 0)):
            with self.assertRaises(ValueError): response(self.x, self.x, self.rate, *args)

    def test_wav_hashes_preservation_and_rate_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = [Path(d)/name for name in ('a.wav','b.wav')]
            def write(path, rate):
                with wave.open(str(path), 'wb') as w:
                    w.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
                    w.writeframes(np.rint(self.x*32768).astype('<i2').tobytes())
            write(a, self.rate); write(b, self.rate)
            before = [p.read_bytes() for p in (a,b)]
            r = analyze(a,b,100,10000)
            self.assertEqual(r['reference_sha256'],r['return_sha256'])
            self.assertEqual(before,[p.read_bytes() for p in (a,b)])
            write(b, 96000)
            with self.assertRaises(ValueError): analyze(a,b)


if __name__ == '__main__': unittest.main()
