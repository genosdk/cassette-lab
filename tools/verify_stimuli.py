#!/usr/bin/env python3
"""Read-only verification of a complete generated stimulus set. Python 3.11+."""
import argparse
import hashlib
import json
from pathlib import Path
import wave
from generate_stimuli import SAMPLE_RATES, specifications


def verify(root):
    errors = []
    expected = {s[0] + '.wav': s for s in specifications()}
    manifest_path = root / 'manifest.json'
    if manifest_path.is_symlink():
        return {'ok': False, 'errors': ['Manifest must not be a symbolic link']}
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, ValueError) as exc:
        return {'ok': False, 'errors': [f'Cannot read manifest: {exc}']}
    if not isinstance(manifest, list):
        return {'ok': False, 'errors': ['Manifest must be an array']}
    seen, rates = set(), set()
    for row in manifest:
        if not isinstance(row, dict) or not isinstance(row.get('file'), str):
            errors.append('Invalid manifest entry')
            continue
        name = row['file']
        # Only exact known basenames are allowed; never follow manifest paths.
        if name not in expected:
            errors.append(f'Unexpected manifest filename: {name}')
            continue
        if name in seen:
            errors.append(f'Duplicate manifest entry: {name}')
            continue
        seen.add(name)
        path = root / name
        if path.is_symlink():
            errors.append(f'{name}: symbolic links are not supported')
            continue
        rate = row.get('sample_rate')
        if type(rate) is not int or rate not in SAMPLE_RATES:
            errors.append(f'{name}: unsupported sample rate')
            continue
        rates.add(rate)
        spec = expected[name]
        metadata = {'channels': 1, 'bits': 24, 'active_seconds': spec[1],
                    'padding_seconds_each': 2, 'peak_dbfs': spec[2]}
        if any(row.get(k) != v for k, v in metadata.items()):
            errors.append(f'{name}: metadata differs from protocol')
        try:
            with path.open('rb') as source:
                digest = hashlib.file_digest(source, 'sha256').hexdigest()
            if digest != row.get('sha256'):
                errors.append(f'{name}: SHA-256 mismatch')
            with wave.open(str(path), 'rb') as audio:
                frames = rate * (spec[1] + 4)
                if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate(),
                    audio.getnframes(), audio.getcomptype()) != (1, 3, rate, frames, 'NONE'):
                    errors.append(f'{name}: WAV header differs from protocol')
                    continue
                padding = rate * 2
                for offset in (0, frames - padding):
                    audio.setpos(offset)
                    data = audio.readframes(padding)
                    if len(data) != padding * 3 or any(data):
                        errors.append(f'{name}: missing or nonzero silence padding')
                audio.setpos(0)
                remaining = frames
                while remaining:
                    count = min(remaining, 8192)
                    data = audio.readframes(count)
                    if len(data) != count * 3:
                        errors.append(f'{name}: truncated audio')
                        break
                    remaining -= count
        except (OSError, ValueError, EOFError, wave.Error) as exc:
            errors.append(f'{name}: {exc}')
    errors.extend(f'Missing manifest entry: {name}' for name in sorted(expected.keys() - seen))
    if len(rates) > 1:
        errors.append('Mixed sample rates in stimulus set')
    extras = {p.name for p in root.iterdir() if p.suffix.lower() == '.wav'} - expected.keys()
    errors.extend(f'Unexpected WAV: {name}' for name in sorted(extras))
    return {'ok': not errors, 'expected_files': len(expected), 'listed_files': len(manifest),
            'sample_rates': sorted(rates), 'errors': errors}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    report = verify(args.folder)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['ok'] else 1)
