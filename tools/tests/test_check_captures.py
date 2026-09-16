import importlib.util
from pathlib import Path
import shutil
import struct
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('check_captures', Path(__file__).parents[1] / 'check_captures.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def wav(path, payload, encoding=1, bits=24, channels=1):
    width = bits // 8
    fmt = struct.pack('<HHIIHH', encoding, channels, 96000, 96000*channels*width, channels*width, bits)
    body = b'WAVEfmt ' + struct.pack('<I', len(fmt)) + fmt + b'data' + struct.pack('<I', len(payload)) + payload
    if len(payload) & 1: body += b'\0'
    path.write_bytes(b'RIFF' + struct.pack('<I', len(body)) + body)


class IntakeTests(unittest.TestCase):
    def test_pcm_channels_and_hash_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'stereo.wav'
            wav(path, b''.join(v.to_bytes(3, 'little', signed=True) for v in (4194304, 0, -4194304, 8388607)), channels=2)
            original = path.read_bytes()
            row = module.inspect(path)
            self.assertEqual(row['frames'], 2)
            self.assertEqual(row['channel_stats'][0]['rms'], .5)
            self.assertEqual(row['channel_stats'][0]['dc_offset'], 0)
            self.assertEqual(row['channel_stats'][1]['full_scale_samples'], 1)
            self.assertEqual(original, path.read_bytes())

    def test_float_invalid_and_overrange(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'float.wav'
            wav(path, struct.pack('<fff', .25, 1.25, float('nan')), encoding=3, bits=32)
            row = module.inspect(path)
            self.assertEqual(row['channel_stats'][0]['nonfinite_samples'], 1)
            self.assertEqual(row['channel_stats'][0]['full_scale_samples'], 1)

    def test_inventory_duplicate_silence_and_truncation(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            wav(root/'a.wav', bytes(6))
            shutil.copyfile(root/'a.wav', root/'b.wav')
            (root/'bad.wav').write_bytes((root/'a.wav').read_bytes()[:-2])
            rows = module.inventory(root)
            self.assertTrue(any('Silent' in w for w in rows[0]['warnings']))
            self.assertTrue(any('duplicate' in w for w in rows[1]['warnings']))
            self.assertIn('error', rows[2])


if __name__ == '__main__': unittest.main()
