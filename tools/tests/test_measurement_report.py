from pathlib import Path
import json
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).parents[1]))
from compile_measurement_report import compile_report


FIXTURES = {
    'alignment': {'accepted': True, 'delay_samples': 4, 'signed_correlation': .99, 'overlap_samples': 100},
    'tone': {'accepted': True, 'fundamental_peak': .1, 'harmonics': [], 'residual_rms': .001},
    'drift': {'accepted': True, 'nominal_frequency_hz': 3150, 'windows': [], 'window_seconds': .1},
    'noise': {'accepted': True, 'power_density_fs2_per_hz': [], 'band_rms': .001, 'segment_samples': 8192},
    'sweep': {'accepted': True, 'magnitude_gain_db': [], 'reference_excited': [], 'reference_floor_db': -60},
}


class MeasurementReportTests(unittest.TestCase):
    def write(self, root, name, value):
        path = root/f'{name}.json'; path.write_text(json.dumps(value)); return path

    def test_complete_accepted_set_and_hashes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); items=[]
            for name, value in FIXTURES.items(): items.append((name, self.write(root,name,value)))
            before={p:p.read_bytes() for _,p in items}
            r=compile_report(items,'synthetic-001')
            self.assertTrue(r['complete_analysis_set']); self.assertTrue(r['all_accepted'])
            self.assertTrue(r['report_ready_for_review'])
            self.assertEqual(r['missing_analysis_types'],[])
            self.assertTrue(all(len(x['report_sha256'])==64 for x in r['reports']))
            self.assertEqual(before,{p:p.read_bytes() for _,p in items})

    def test_partial_and_review_status(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); value=dict(FIXTURES['tone'],accepted=False)
            r=compile_report([('tone-return',self.write(root,'tone',value))],'s')
            self.assertFalse(r['complete_analysis_set']); self.assertFalse(r['all_accepted'])
            self.assertFalse(r['report_ready_for_review'])
            self.assertEqual(r['review_labels'],['tone-return'])
            self.assertIn('sweep',r['missing_analysis_types'])

    def test_repeated_types_allowed_but_labels_unique(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); a=self.write(root,'a',FIXTURES['tone']); b=self.write(root,'b',FIXTURES['tone'])
            r=compile_report([('100hz',a),('1khz',b)],'s')
            self.assertEqual(r['analysis_counts']['tone'],2)
            with self.assertRaises(ValueError): compile_report([('tone',a),('tone',b)],'s')

    def test_rejects_unknown_ambiguous_and_nonboolean(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            bad=[{'accepted':True}, dict(FIXTURES['tone'], **FIXTURES['noise']),
                 dict(FIXTURES['tone'],accepted=1), []]
            for i,value in enumerate(bad):
                with self.assertRaises(ValueError): compile_report([('x',self.write(root,str(i),value))],'s')

    def test_rejects_duplicate_keys_and_nonfinite_json(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name,text in [('dup','{"accepted":true,"accepted":false}'),
                              ('nan','{"accepted":true,"x":NaN}')]:
                p=root/f'{name}.json'; p.write_text(text)
                with self.assertRaises(ValueError): compile_report([('x',p)],'s')

    def test_requires_inputs_and_session(self):
        with self.assertRaises(ValueError): compile_report([], 's')
        with self.assertRaises(ValueError): compile_report([('x',Path('missing'))], '')


if __name__ == '__main__': unittest.main()
