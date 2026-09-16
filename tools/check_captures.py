#!/usr/bin/env python3
"""Read-only WAV intake inventory. Python standard library; no audio rewriting."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct


def inspect(path):
    result = {'file': str(path), 'warnings': []}
    with path.open('rb') as source:
        result['sha256'] = hashlib.file_digest(source, 'sha256').hexdigest()
        size = source.tell()
        source.seek(0)
        header = source.read(12)
        if len(header) != 12 or header[:4] != b'RIFF' or header[8:] != b'WAVE':
            raise ValueError('Expected RIFF/WAVE (RF64 and compressed formats unsupported)')
        end = 8 + struct.unpack_from('<I', header, 4)[0]
        if end > size:
            raise ValueError('Truncated RIFF container')
        fmt = None
        data = None
        while source.tell() + 8 <= end:
            tag, count = struct.unpack('<4sI', source.read(8))
            offset = source.tell()
            if offset + count > end:
                raise ValueError('Truncated WAV chunk')
            if tag == b'fmt ':
                fmt = source.read(min(count, 40))
            elif tag == b'data':
                if data is not None:
                    raise ValueError('Multiple data chunks unsupported')
                data = offset, count
            source.seek(offset + count + (count & 1))
        if fmt is None or len(fmt) < 16 or data is None:
            raise ValueError('Missing fmt or data chunk')
        encoding, channels, rate, byte_rate, align, bits = struct.unpack_from('<HHIIHH', fmt)
        if encoding == 65534:
            if len(fmt) < 40 or fmt[26:40] != bytes.fromhex('000000001000800000aa00389b71'):
                raise ValueError('Unsupported extensible WAV subtype')
            valid_bits = struct.unpack_from('<H', fmt, 18)[0]
            if valid_bits not in (0, bits):
                raise ValueError('Packed valid-bit formats unsupported')
            encoding = struct.unpack_from('<H', fmt, 24)[0]
        if (encoding == 1 and bits not in (16, 24, 32)) or (encoding == 3 and bits != 32) or encoding not in (1, 3):
            raise ValueError('Supported formats: PCM 16/24/32-bit or float 32-bit')
        width = bits // 8
        if not channels or not rate or align != channels * width or byte_rate != rate * align:
            raise ValueError('Invalid WAV format dimensions')
        if data[1] % align:
            raise ValueError('Incomplete sample frame')
        frames = data[1] // align
        stats = [dict(peak=0., squares=0., total=0., full_scale_samples=0, nonfinite_samples=0) for _ in range(channels)]
        source.seek(data[0])
        remaining = data[1]
        while remaining:
            block = source.read(min(align * 4096, remaining))
            remaining -= len(block)
            for i in range(0, len(block), width):
                if encoding == 1:
                    value = int.from_bytes(block[i:i+width], 'little', signed=True) / (2 ** (bits-1))
                    threshold = 1 - 1 / (2 ** (bits-1))
                else:
                    value = struct.unpack_from('<f' if bits == 32 else '<d', block, i)[0]
                    threshold = 1.
                s = stats[(i // width) % channels]
                if not math.isfinite(value):
                    s['nonfinite_samples'] += 1
                    continue
                s['peak'] = max(s['peak'], abs(value))
                s['squares'] += value * value
                s['total'] += value
                s['full_scale_samples'] += abs(value) >= threshold
        result.update(sample_rate=rate, channels=channels, bits=bits,
                      encoding='PCM' if encoding == 1 else 'float', frames=frames, seconds=frames/rate)
        for s in stats:
            s['rms'] = math.sqrt(s.pop('squares') / max(1, frames))
            s['dc_offset'] = s.pop('total') / max(1, frames)
            s['peak_dbfs'] = 20*math.log10(s['peak']) if s['peak'] else None
        result['channel_stats'] = stats
        if rate != 96000: result['warnings'].append('Sample rate differs from requested 96000 Hz')
        if channels != 1: result['warnings'].append('Expected mono capture; review channel routing')
        if not frames: result['warnings'].append('Empty audio')
        if any(s['peak'] == 0 for s in stats): result['warnings'].append('Silent channel; review unless intentional')
        if any(s['full_scale_samples'] for s in stats): result['warnings'].append('Full-scale samples: review possible digital clipping')
        if any(s['nonfinite_samples'] for s in stats): result['warnings'].append('Invalid nonfinite audio samples')
    return result


def inventory(root):
    rows, seen = [], {}
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.suffix.lower() != '.wav': continue
        try:
            row = inspect(path)
            digest = row['sha256']
            if digest in seen: row['warnings'].append('Byte-identical duplicate of ' + seen[digest])
            else: seen[digest] = str(path.relative_to(root))
        except (ValueError, OSError, struct.error) as exc:
            row = {'error': str(exc)}
        row['file'] = str(path.relative_to(root))
        rows.append(row)
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    if not args.folder.is_dir(): parser.error('folder must be an existing directory')
    rows = inventory(args.folder)
    print(json.dumps({'files': rows, 'count': len(rows)}, indent=2, allow_nan=False))
    raise SystemExit(1 if not rows or any('error' in row for row in rows) else 0)
