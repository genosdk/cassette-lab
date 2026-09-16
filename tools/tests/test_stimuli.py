import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave

sys.path.insert(0, str(Path(__file__).parents[1]))
import generate_stimuli as generator
import verify_stimuli as verifier

# Short synthetic fixture; full production names/durations are checked separately.
SPEC = ('reference_1000_m18', 1, -18, 1000, 1000)


class StimulusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def create_set(self):
        with patch.object(generator, 'specifications', return_value=[SPEC]), contextlib.redirect_stdout(io.StringIO()):
            generator.generate(self.root, 48000)

    def verify(self):
        with patch.object(verifier, 'specifications', return_value=[SPEC]):
            return verifier.verify(self.root)

    def test_signal_format_headroom_padding_and_determinism(self):
        a, b = self.root / 'a.wav', self.root / 'b.wav'
        generator.write_signal(a, 48000, SPEC)
        generator.write_signal(b, 48000, SPEC)
        self.assertEqual(a.read_bytes(), b.read_bytes())
        with wave.open(str(a), 'rb') as audio:
            self.assertEqual((audio.getnchannels(), audio.getsampwidth(), audio.getframerate(), audio.getnframes()), (1, 3, 48000, 240000))
            self.assertEqual(audio.readframes(96000), bytes(288000))
            data = audio.readframes(48000)
            values = [int.from_bytes(data[i:i+3], 'little', signed=True) for i in range(0, len(data), 3)]
            self.assertEqual(values[0], 0)
            self.assertEqual(values[-1], 0)
            self.assertAlmostEqual(max(map(abs, values)) / 8388607, 10 ** (-18 / 20), places=6)
            self.assertEqual(audio.readframes(96000), bytes(288000))

    def test_refuses_overwrite_and_invalid_rate_without_changes(self):
        original = b'preserve this recording'
        target = self.root / 'recording.wav'
        target.write_bytes(original)
        with self.assertRaises(FileExistsError): generator.generate(self.root, 96000)
        self.assertEqual(target.read_bytes(), original)
        self.assertEqual(list(self.root.iterdir()), [target])
        with self.assertRaises(FileExistsError): generator.write_signal(target, 48000, SPEC)
        self.assertEqual(target.read_bytes(), original)
        new = self.root / 'new'
        with self.assertRaises(ValueError): generator.generate(new, 8000)
        self.assertFalse(new.exists())

    def test_verify_valid_then_tampered_audio(self):
        self.create_set()
        self.assertTrue(self.verify()['ok'])
        path = self.root / (SPEC[0] + '.wav')
        data = bytearray(path.read_bytes())
        data[44 + 96000 * 3 + 3000] ^= 1
        path.write_bytes(data)
        before = path.read_bytes()
        self.assertTrue(any('SHA-256' in e for e in self.verify()['errors']))
        self.assertEqual(path.read_bytes(), before)

    def test_manifest_missing_duplicate_and_path_escape(self):
        self.create_set()
        manifest_path = self.root / 'manifest.json'
        rows = json.loads(manifest_path.read_text())
        manifest_path.write_text(json.dumps(rows + rows + [{'file': '../outside.wav'}]))
        errors = self.verify()['errors']
        self.assertTrue(any('Duplicate' in e for e in errors))
        self.assertTrue(any('Unexpected manifest' in e for e in errors))
        manifest_path.write_text('[]')
        self.assertTrue(any('Missing manifest' in e for e in self.verify()['errors']))

    def test_padding_and_header_checked_even_with_updated_hash(self):
        self.create_set()
        path = self.root / (SPEC[0] + '.wav')
        data = bytearray(path.read_bytes())
        data[44] = 1
        path.write_bytes(data)
        manifest_path = self.root / 'manifest.json'
        rows = json.loads(manifest_path.read_text())
        rows[0]['sha256'] = hashlib.sha256(data).hexdigest()
        manifest_path.write_text(json.dumps(rows))
        self.assertTrue(any('padding' in e for e in self.verify()['errors']))
        data[24:28] = (96000).to_bytes(4, 'little')
        path.write_bytes(data)
        self.assertTrue(any('header' in e for e in self.verify()['errors']))

    def test_missing_and_invalid_manifest(self):
        self.assertFalse(self.verify()['ok'])
        (self.root / 'manifest.json').write_text('{}')
        self.assertFalse(self.verify()['ok'])

    def test_protocol_has_18_unique_signals_below_nyquist(self):
        specs = generator.specifications()
        self.assertEqual(len(specs), 18)
        self.assertEqual(len({s[0] for s in specs}), 18)
        self.assertTrue(all(max(s[3:]) < min(generator.SAMPLE_RATES) / 2 for s in specs))


if __name__ == '__main__': unittest.main()
