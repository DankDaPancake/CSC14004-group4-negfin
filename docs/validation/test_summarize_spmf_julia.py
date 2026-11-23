"""Strict evidence selection: no fabricated points for incomplete campaigns."""
import copy
import csv
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'bench'))
import spmf_campaign as c
spec = importlib.util.spec_from_file_location('spmf_summary', Path(__file__).with_name('summarize-spmf-julia.py'))
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.campaign = self.root / 'campaign'
        self.campaign.mkdir()
        self.meta = dict(schema_version=1, fingerprint='fp', config={'selected': {'Chess': ['0.9']}},
                         datasets={'Chess': {'input_sha256': 'a' * 64, 'n_transactions': 10}})
        self.save('campaign.json', self.meta)
        case = dict(dataset='Chess', minsup='0.9', scope='main')
        self.condition_dir = self.campaign / 'conditions' / c._condition_id('main', case)
        self.condition_dir.mkdir(parents=True)
        self.rows = []
        for variant in ('spmf', 'optimized'):
            for repetition, wall in enumerate((1.0, 5.0, 3.0), 1):
                aid = f'{variant}-{repetition}'
                row = dict(schema_version=1, fingerprint='fp', attempt_id=aid,
                    scope='main', dataset='Chess', minsup='0.9', min_count=9,
                    input_sha256='a' * 64, n_transactions=10, repetition=repetition,
                    variant=variant, status='ok', exit_code=0, process_wall_seconds=wall,
                    maxrss_bytes=1048576 * repetition, output_bytes=100,
                    rss_method='Windows GetProcessMemoryInfo.PeakWorkingSetSize')
                self.rows.append(row)
                self.save(f'attempts/{aid}/measurement.json', row)
                self.save(f'attempts/{aid}/validation.json', row | dict(ok=True, count=2,
                          canonical_sha256='b' * 64, source_sha256='c' * 64))
        self.condition = dict(fingerprint='fp', equal=True, count=2, repetitions=3,
                              attempts=[r['attempt_id'] for r in self.rows])
        self.comparison = dict(fingerprint='fp', equal=True, missing=0, extra=0, support_mismatch=0)
        self.save_condition()
        self.write_rows()

    def save(self, relative, value):
        path = self.campaign / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding='utf-8')

    def save_condition(self):
        (self.condition_dir / 'condition.json').write_text(json.dumps(self.condition))
        (self.condition_dir / 'comparison.json').write_text(json.dumps(self.comparison))

    def write_rows(self):
        path = self.campaign / 'runs.csv'
        path.unlink(missing_ok=True)
        for row in self.rows:
            c.append_measurement(path, row)

    def test_known_medians_ranges_and_units(self):
        accepted, incomplete = s.summarize(self.campaign)
        self.assertEqual(incomplete, [])
        self.assertEqual(len(accepted), 2)
        for row in accepted:
            self.assertEqual(row['wall_median_seconds'], 3.0)
            self.assertEqual(row['wall_min_seconds'], 1.0)
            self.assertEqual(row['wall_max_seconds'], 5.0)
            self.assertEqual(row['rss_median_mib'], 2.0)
            self.assertEqual(row['n_patterns'], 2)
            self.assertEqual(row['repetitions'], 3)

    def test_error_or_missing_repeat_never_becomes_zero(self):
        for mutation in ('error', 'missing', 'duplicate', 'mixed'):
            with self.subTest(mutation=mutation):
                original = copy.deepcopy(self.rows)
                if mutation == 'error':
                    self.rows[0]['status'] = 'timeout'
                elif mutation == 'missing':
                    self.rows.pop()
                elif mutation == 'duplicate':
                    self.rows[1]['repetition'] = 1
                else:
                    self.rows[0]['fingerprint'] = 'other'
                self.write_rows()
                good, bad = s.summarize(self.campaign)
                self.assertEqual(good, [])
                self.assertEqual(len(bad), 1)
                self.rows = original

    def test_consistently_wrong_input_or_threshold_rejected_against_campaign(self):
        # All rows agree with one another, but must still match frozen input/ceil.
        for row in self.rows:
            row['min_count'] = 8  # exact ceil(.9 * 10) is 9
            self.save(f"attempts/{row['attempt_id']}/measurement.json", row)
        self.write_rows()
        good, bad = s.summarize(self.campaign)
        self.assertEqual(good, [])
        self.assertEqual(len(bad), 1)

    def test_missing_exact_comparison_rejects_whole_pair(self):
        (self.condition_dir / 'comparison.json').unlink()
        good, bad = s.summarize(self.campaign)
        self.assertEqual(good, [])
        self.assertEqual(len(bad), 1)

    def test_mismatched_count_or_digest_rejected(self):
        path = self.campaign / 'attempts/spmf-2/validation.json'
        data = json.loads(path.read_text())
        for change in ({'count': 9}, {'canonical_sha256': 'd' * 64}, {'fingerprint': 'bad'}):
            path.write_text(json.dumps(data | change))
            good, bad = s.summarize(self.campaign)
            self.assertEqual(good, [])
            self.assertEqual(len(bad), 1)

    def test_nonfinite_or_negative_metrics_rejected(self):
        for metric in ('process_wall_seconds', 'maxrss_bytes'):
            self.rows[0][metric] = -1
            self.write_rows()
            good, bad = s.summarize(self.campaign)
            self.assertEqual(good, [])
            self.assertEqual(len(bad), 1)

    def test_old_scope_excluded_without_filling_missing_slot(self):
        self.rows[-1]['scope'] = 'warm'
        self.write_rows()
        good, bad = s.summarize(self.campaign)
        self.assertEqual(good, [])
        self.assertEqual(len(bad), 1)

    def test_figures_export_png_pdf_only_from_accepted_summary(self):
        try:
            import matplotlib
        except ImportError:
            self.skipTest('Run in approved plotting venv for PNG/PDF test')
        rows, _ = s.summarize(self.campaign)
        config = {'selected': {'Chess': ['0.9', '0.8', '0.7', '0.6', '0.5', '0.4', '0.3']}}
        # Fixture only: add a fourth selected point; no real-data publication.
        rows += [dict(row, minsup='0.6') for row in rows]
        out = self.root / 'figures'
        paths = s.render_figures(rows, config, out)
        self.assertEqual(len(paths), 6)
        for path in paths:
            content = Path(path).read_bytes()
            self.assertTrue(content.startswith(b'%PDF') if str(path).endswith('.pdf')
                            else content.startswith(b'\x89PNG\r\n\x1a\n'))
        self.assertIn('Median of 3', (out / 'captions.md').read_text())
        empty = self.root / 'empty'
        self.assertEqual(s.render_figures([], config, empty), [])
        self.assertFalse(empty.exists())

    def test_package_excludes_large_inputs_and_verifies_manifest(self):
        self.save('attempts/spmf-1/output.txt', {'large': 'do not package'})
        (self.campaign / 'fixtures').mkdir()
        (self.campaign / 'fixtures/input.txt').write_text('1 2\n')
        target = self.root / 'handoff.zip'
        result = s.package_campaign(self.campaign, target)
        self.assertEqual(len(result['sha256']), 64)
        self.assertGreater(result['files'], 5)
        with zipfile.ZipFile(target) as archive:
            self.assertIsNone(archive.testzip())
            self.assertNotIn('attempts/spmf-1/output.txt', archive.namelist())
            self.assertNotIn('fixtures/input.txt', archive.namelist())
            self.assertIn('SHA256SUMS.txt', archive.namelist())
        with self.assertRaises(FileExistsError):
            s.package_campaign(self.campaign, target)


if __name__ == '__main__':
    unittest.main()
