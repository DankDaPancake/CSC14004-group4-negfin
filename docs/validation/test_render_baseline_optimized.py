import importlib.util
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    'render_baseline_optimized', Path(__file__).with_name('render-baseline-optimized.py'))
render = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(render)


class PairedBenchmarkRenderTests(unittest.TestCase):
    def test_load_runs_excludes_interrupted_rows_and_merges_run_directories(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for run_id, rows in (
                ('baseline', [
                    ('baseline', 'cold', '1.0', '10', '100', '0.1', 'ok'),
                    ('baseline', 'cold', '2.0', '12', '110', '0.1', 'ok'),
                    ('baseline', 'scalability-cold', '0.1', '5', '50', '0.99', 'ok'),
                    ('baseline', 'scalability-warm', '0.1', '', '', '0.99', 'ok'),
                    ('baseline', 'scalability-warm', '0.1', '', '', '0.45', 'error'),
                ]),
                ('optimized', [
                    ('optimized', 'cold', '1', '6', '90', '0.1', 'ok'),
                    ('optimized', 'scalability-cold', '0.1', '3', '40', '0.99', 'ok'),
                ]),
            ):
                run = root / run_id
                run.mkdir()
                with (run / 'runs.csv').open('w', encoding='utf-8', newline='') as stream:
                    stream.write('run_id,variant,scope,dataset,fraction,minsup,process_wall_seconds,maxrss_bytes,n_patterns,input_sha256,status\n')
                    for variant, scope, fraction, wall, rss, minsup, status in rows:
                        stream.write(f'{run_id},{variant},{scope},Chess,{fraction},{minsup},{wall},{rss},7,hash-{fraction},{status}\n')
            records = render.load_runs(root)
            self.assertEqual(len(records), 7)
            cold = render.aggregate(records, scope='cold', metric='process_wall_seconds')
            self.assertEqual(cold[('Chess', '0.1', '1.0', 'baseline')]['median'], 10)
            scale = render.aggregate(records, scope='scalability-cold', metric='maxrss_bytes')
            self.assertEqual(scale[('Chess', '0.99', '0.1', 'baseline')]['median'], 50)

    def test_scale_pair_hash_mismatch_fails_closed(self):
        rows = [
            dict(variant='baseline', scope='scalability-cold', dataset='Chess', minsup='0.99', fraction='0.1',
                 input_sha256='left', process_wall_seconds='1', maxrss_bytes='2', status='ok'),
            dict(variant='optimized', scope='scalability-cold', dataset='Chess', minsup='0.99', fraction='0.1',
                 input_sha256='right', process_wall_seconds='1', maxrss_bytes='2', status='ok'),
        ]
        with self.assertRaisesRegex(ValueError, 'subset SHA256 mismatch'):
            render.validate_paired_scale_hashes(rows)

    def test_svg_render_includes_both_variants_and_accessible_table(self):
        rows = [
            dict(variant='baseline', scope='scalability-cold', dataset='T10I4D100K', minsup='0.004', fraction=f,
                 input_sha256=f'hash-{f}', process_wall_seconds=str(i + 1), maxrss_bytes=str((i + 1) * 1024**2),
                 n_patterns='2001', status='ok')
            for i, f in enumerate(('0.1', '0.25', '0.5', '0.75', '1.0'))
        ] + [
            dict(variant='optimized', scope='scalability-cold', dataset='T10I4D100K', minsup='0.004', fraction=f,
                 input_sha256=f'hash-{f}', process_wall_seconds=str((i + 1) / 2), maxrss_bytes=str((i + 1) * 2 * 1024**2),
                 n_patterns='2001', status='ok')
            for i, f in enumerate(('0.1', '0.25', '0.5', '0.75', '1.0'))
        ]
        for dataset in ('Accidents', 'Mushroom', 'Retail', 'Chess'):
            rows.extend([dict(r, dataset=dataset) for r in rows if r['dataset'] == 'T10I4D100K'])
        svg = render.scalability_svg(rows)
        self.assertIn('Baseline', svg)
        self.assertIn('Optimized', svg)
        self.assertIn('<table', svg)
        self.assertIn('T10I4D100K', svg)


if __name__ == '__main__':
    unittest.main()
