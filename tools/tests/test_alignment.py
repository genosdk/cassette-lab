import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
import wave
import numpy as np
sys.path.insert(0, str(Path(__file__).parents[1]))
from analyze_alignment import analyze, estimate, read_mono


class AlignmentTests(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(718)
        self.x = self.rng.uniform(-.2, .2, 8192)

    def test_known_delays_gain_dc_noise_and_polarity(self):
        for delay in (-317, 0, 421):
            for gain in (.5, -.7):
                y = np.r_[np.zeros(delay), self.x] if delay >= 0 else self.x[-delay:]
                y = gain*y + .01 + self.rng.normal(0, .0001, len(y))
                result = estimate(self.x, y, 48000, .02)
                self.assertTrue(result['accepted'], result)
                self.assertEqual(result['delay_samples'], delay)
                self.assertAlmostEqual(result['relative_gain_linear'], gain, places=4)
                self.assertEqual(result['polarity'], 'normal' if gain > 0 else 'inverted')

    def test_periodic_tone_is_ambiguous(self):
        tone = .2*np.sin(2*np.pi*1000*np.arange(8192)/48000)
        result = estimate(tone, np.roll(tone, 96), 48000, .02)
        self.assertFalse(result['accepted'])
        self.assertIsNone(result['relative_gain_linear'])
        self.assertTrue(any('Ambiguous' in s for s in result['warnings']))

    def test_unrelated_audio_and_boundary_are_flagged(self):
        result = estimate(self.x, self.rng.uniform(-.2,.2,8192),48000,.02)
        self.assertFalse(result['accepted'])
        result = estimate(self.x,np.r_[np.zeros(480),self.x],48000,.01)
        self.assertEqual(result['delay_samples'],480)
        self.assertTrue(any('boundary' in s for s in result['warnings']))

    def test_invalid_audio(self):
        for bad in (np.zeros(8192), np.ones(8192)*.1, np.full(8192,np.nan), np.ones(8192), np.zeros(12)):
            with self.assertRaises(ValueError): estimate(self.x,bad,48000)
        with self.assertRaises(ValueError): estimate(self.x,self.x,48000,float('nan'))

    def test_pcm_widths_and_end_to_end_files_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for width in (2,3,4):
                paths = [root/f'source{width}.wav',root/f'capture{width}.wav']
                for path, signal in zip(paths,(self.x,np.r_[np.zeros(211),self.x*.5])):
                    values = np.rint(signal*(2**(width*8-1))).astype(np.int64)
                    data = b''.join(int(v).to_bytes(width,'little',signed=True) for v in values)
                    with wave.open(str(path),'wb') as w:
                        w.setparams((1,width,48000,0,'NONE','not compressed'));w.writeframes(data)
                before = [p.read_bytes() for p in paths]
                result = analyze(*paths,max_delay_seconds=.02)
                self.assertTrue(result['accepted'])
                self.assertEqual(result['delay_samples'],211)
                self.assertEqual(result['source_sha256'],hashlib.sha256(before[0]).hexdigest())
                self.assertEqual([p.read_bytes() for p in paths],before)
                changed = bytearray(paths[1].read_bytes());changed[24:28]=(96000).to_bytes(4,'little')
                paths[1].write_bytes(changed)
                with self.assertRaises(ValueError):analyze(*paths)


if __name__ == '__main__': unittest.main()
