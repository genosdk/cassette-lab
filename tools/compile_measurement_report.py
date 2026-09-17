#!/usr/bin/env python3
"""Combine read-only analyzer JSON outputs into one provenance-preserving report."""
import argparse
import hashlib
import json
from pathlib import Path

REQUIRED = ('alignment', 'tone', 'drift', 'noise', 'sweep')
SIGNATURES = {
    'alignment': {'delay_samples', 'signed_correlation', 'overlap_samples'},
    'tone': {'fundamental_peak', 'harmonics', 'residual_rms'},
    'drift': {'nominal_frequency_hz', 'windows', 'window_seconds'},
    'noise': {'power_density_fs2_per_hz', 'band_rms', 'segment_samples'},
    'sweep': {'magnitude_gain_db', 'reference_excited', 'reference_floor_db'},
}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def _load(path):
    raw = Path(path).read_bytes()
    try:
        value = json.loads(raw, object_pairs_hook=_unique_object,
                           parse_constant=lambda x: (_ for _ in ()).throw(ValueError(f'Invalid JSON number: {x}')))
    except UnicodeDecodeError as exc:
        raise ValueError(f'{path}: JSON must be UTF-8') from exc
    if not isinstance(value, dict):
        raise ValueError(f'{path}: top-level JSON value must be an object')
    if type(value.get('accepted')) is not bool:
        raise ValueError(f'{path}: accepted must be a JSON boolean')
    matches = [name for name, keys in SIGNATURES.items() if keys <= value.keys()]
    if len(matches) != 1:
        raise ValueError(f'{path}: expected exactly one recognized analyzer schema')
    return raw, value, matches[0]


def compile_report(items, session):
    if not isinstance(session, str) or not session.strip():
        raise ValueError('Session identifier must be nonempty')
    if not items:
        raise ValueError('At least one analyzer report is required')
    labels = set(); entries = []; counts = {name: 0 for name in REQUIRED}
    for label, path in items:
        if not label or label in labels:
            raise ValueError(f'Duplicate or empty label: {label!r}')
        labels.add(label)
        raw, result, kind = _load(path)
        counts[kind] += 1
        entries.append({'label': label, 'analysis': kind,
                        'report_file': Path(path).name,
                        'report_sha256': hashlib.sha256(raw).hexdigest(),
                        'accepted': result['accepted'], 'result': result})
    missing = [name for name, count in counts.items() if count == 0]
    review = [entry['label'] for entry in entries if not entry['accepted']]
    return {'schema': 'cassette-lab.measurement-report.v1', 'session': session,
            'complete_analysis_set': not missing, 'all_accepted': not review,
            'report_ready_for_review': not missing and not review,
            'analysis_counts': counts, 'missing_analysis_types': missing,
            'review_labels': review, 'reports': entries,
            'status_meaning': 'Ready for review means all five analyzer types are present and each analyzer accepted its own numerical checks; it is not hardware calibration or proof of capture validity.'}


def _input(value):
    if '=' not in value:
        raise argparse.ArgumentTypeError('Use LABEL=REPORT.json')
    label, path = value.split('=', 1)
    if not label or not path:
        raise argparse.ArgumentTypeError('Use nonempty LABEL=REPORT.json')
    return label, Path(path)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--session', required=True)
    p.add_argument('--input', action='append', type=_input, required=True,
                   metavar='LABEL=REPORT.json')
    a = p.parse_args()
    try:
        report = compile_report(a.input, a.session)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        p.exit(1, f'Report compilation failed: {exc}\n')
    print(json.dumps(report, indent=2, allow_nan=False))
    raise SystemExit(0 if report['report_ready_for_review'] else 2)
