"""Campaign invariants and real-process evidence lifecycle tests."""
import csv
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

BENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BENCH))
spec = importlib.util.spec_from_file_location('spmf_campaign', BENCH / 'spmf_campaign.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class CampaignTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = BENCH.parent
        self.config = BENCH / 'config-spmf-julia-20261122.toml'

    def test_exact_threshold_and_float_boundary(self):
        self.assertEqual(c.expected_min_count('0.07', 100), 7)
        self.assertEqual(c.expected_min_count('0.004', 88162), 353)
        self.assertEqual(c.threshold_info('0.07', 100),
                         dict(exact=7, binary_ceil=8, matches=False))
        for bad in ('0', '1.1', 'NaN', '-0.1'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                c.expected_min_count(bad, 100)

    def test_explicit_spmf_ratio_mapping_preserves_absolute_threshold(self):
        mapped = c.spmf_ratio('0.07', 100)
        self.assertEqual(mapped['requested'], '0.07')
        self.assertEqual(mapped['effective'], '0.06999999999999999')
        self.assertEqual(mapped['min_count'], 7)
        self.assertEqual(c.spmf_ratio('0.9', 3196)['effective'], '0.9')

    def test_schedule_exact_slots_and_alternating_order(self):
        config = c.load_campaign(self.config, self.repo)
        slots = c.schedule(config)
        self.assertEqual(len(slots), 210)
        keys = {(x['dataset'], x['minsup'], x['repetition'], x['variant']) for x in slots}
        self.assertEqual(len(keys), 210)
        self.assertEqual([x['variant'] for x in slots[:6]],
                         ['spmf', 'optimized', 'optimized', 'spmf', 'spmf', 'optimized'])
        self.assertEqual(slots[0]['minsup'], '0.9')

    def test_config_cannot_silently_change_selected_levels(self):
        text = self.config.read_text()
        other = self.root / 'changed.toml'
        other.write_text(text.replace('"0.55"', '"0.54"'))
        with self.assertRaisesRegex(ValueError, 'selected'):
            c.load_campaign(other, self.repo)

    def test_input_hash_and_count_with_bom_comments(self):
        path = self.root / 'input.txt'
        path.write_bytes(b'\xef\xbb\xbf@meta\n#comment\n1 2\n\n2 3\n')
        result = c.inspect_input(path)
        self.assertEqual(result['n_transactions'], 2)
        self.assertEqual(len(result['sha256']), 64)
        with self.assertRaisesRegex(ValueError, 'Checksum'):
            c.inspect_input(path, expected_sha256='0' * 64)
        with self.assertRaisesRegex(ValueError, 'transactions'):
            c.inspect_input(path, expected_transactions=3)

    def test_command_argv_keeps_spaces_and_pins_threads(self):
        args = dict(julia=Path('C:/space path/julia.exe'), java=Path('C:/java.exe'),
                    jar=Path('C:/space path/spmf.jar'), repo=self.repo,
                    input_path=Path('C:/data in.txt'), output_path=Path('C:/out file.txt'),
                    stats_path=Path('C:/stats.toml'), minsup='0.004')
        java = c.build_command('spmf', **args)
        self.assertIn('C:\\space path\\spmf.jar', java)
        self.assertIn('-XX:ActiveProcessorCount=1', java)
        self.assertIn('-Xmx4g', java)
        julia = c.build_command('optimized', **args)
        self.assertIn('--threads=1', julia)
        self.assertEqual(julia[julia.index('--variant') + 1], 'optimized')
        with self.assertRaises(ValueError):
            c.build_command('baseline', **args)

    def test_runtime_missing_fails_explicitly(self):
        with self.assertRaisesRegex(ValueError, 'runtime'):
            c.runtime_info(self.root / 'missing', self.root / 'java', self.root / 'jar')

    def test_csv_partial_tail_and_duplicate_slots_rejected(self):
        path = self.root / 'runs.csv'
        row = {key: '' for key in c.RUN_COLUMNS}
        row.update(attempt_id='a', dataset='Chess', minsup='0.9', repetition=1,
                   variant='spmf', scope='main', fingerprint='fp')
        c.append_measurement(path, row)
        self.assertEqual(len(c.read_measurements(path)), 1)
        with path.open('ab') as handle:
            handle.write(b'broken,partial')
        with self.assertRaisesRegex(ValueError, 'CSV'):
            c.read_measurements(path)

    def test_resume_rejects_changed_provenance_and_missing_pilot(self):
        meta = dict(schema_version=1, fingerprint='old')
        (self.root / 'campaign.json').write_text(json.dumps(meta))
        with self.assertRaisesRegex(ValueError, 'provenance'):
            c.check_resume(self.root, {'fingerprint': 'new'})
        with self.assertRaisesRegex(ValueError, 'pilot'):
            c.require_pilot(self.root, 'old')
        (self.root / 'pilot.json').write_text(json.dumps({'fingerprint': 'other', 'ok': True}))
        with self.assertRaisesRegex(ValueError, 'pilot'):
            c.require_pilot(self.root, 'old')

    def test_pilot_requires_hand_checked_fixture_expectations(self):
        expected = c.fixture_expectations()
        self.assertEqual(expected['toy'], {'count': 3, 'records': '1 #SUP: 4\n1 2 #SUP: 2\n2 #SUP: 3\n'})
        self.assertEqual(expected['boundary'], {'count': 2, 'records': '1 #SUP: 7\n2 #SUP: 93\n'})
        self.assertFalse(c.fixture_matches('toy', {'equal': True, 'count': 2,
                                                  'canonical_sha256': 'bad'}))

    def test_changed_sources_block_launch_before_measurement(self):
        source = self.root / 'source.py'
        source.write_bytes(b'old')
        meta = {'sources': {str(source): c._hash(source)}}
        c.verify_sources(meta)
        source.write_bytes(b'new')
        with self.assertRaisesRegex(ValueError, 'source'):
            c.verify_sources(meta)

    def test_failed_or_trial_rows_never_fill_main_slot(self):
        rows = [dict(scope='pilot', dataset='Chess', minsup='0.9', repetition='1',
                     variant='spmf', status='ok', attempt_id='trial', fingerprint='fp')]
        self.assertEqual(c.completed_slots(rows, 'fp'), set())
        rows.append(dict(rows[0], scope='main', status='timeout', attempt_id='failed'))
        # Attempted failure is retained, never retried into a successful slot implicitly.
        self.assertEqual(c.completed_slots(rows, 'fp'), {('Chess', '0.9', 1, 'spmf')})
        with self.assertRaisesRegex(ValueError, 'provenance'):
            c.completed_slots(rows, 'other')

    def test_pilot_rejects_fixture_gate_forgery(self):
        (self.root / 'pilot.json').write_text(json.dumps({'fingerprint': 'fp', 'ok': True}))
        with self.assertRaisesRegex(ValueError, 'pilot'):
            c.require_pilot(self.root, 'fp')

    @unittest.skipUnless(sys.platform == 'win32', 'Windows process integration')
    def test_three_repetitions_detect_nonrepeatable_output(self):
        work = self.root / 'campaign'
        work.mkdir()
        config = c.load_campaign(self.config, self.repo)
        config.update(minimum_free_disk_bytes=1)
        meta = dict(fingerprint='fp', config=config, repo=str(self.repo),
                    runtimes=dict(julia=sys.executable, java=sys.executable, jar='unused'))
        input_path = self.root / 'input.txt'
        input_path.write_text('1\n1\n')
        case = dict(dataset='toy', minsup='0.5', input_path=str(input_path),
                    n_transactions=2, input_sha256=c.inspect_input(input_path)['sha256'])
        calls = []
        def command(variant, **kw):
            calls.append(variant)
            text = '1 #SUP: 1\n' if len(calls) == 3 else '1 #SUP: 2\n'
            return [sys.executable, '-I', '-c',
                    'import pathlib,sys; pathlib.Path(sys.argv[1]).write_bytes(sys.argv[2].encode())',
                    str(kw['output_path']), text]
        with patch.object(c, 'build_command', side_effect=command):
            result = c.run_condition(work, meta, case, scope='main', repetitions=3)
        self.assertFalse(result['equal'])
        self.assertEqual(calls, ['spmf', 'optimized', 'optimized', 'spmf', 'spmf', 'optimized'])
        self.assertEqual(len(c.read_measurements(work / 'runs.csv')), 6)
        rows = c.read_measurements(work / 'runs.csv')
        validation = json.loads((work / 'attempts' / rows[2]['attempt_id'] / 'validation.json').read_text())
        self.assertFalse(validation['ok'])

    @unittest.skipUnless(sys.platform == 'win32', 'Windows process integration')
    def test_real_pair_saves_exact_validation_before_output_cleanup(self):
        work = self.root / 'campaign'
        work.mkdir()
        input_path = self.root / 'input.txt'
        input_path.write_text('1 2\n1\n')
        config = c.load_campaign(self.config, self.repo)
        config.update(minimum_free_disk_bytes=1, validation_chunk_bytes=10)
        meta = dict(fingerprint='fp', config=config, repo=str(self.repo),
                    runtimes=dict(julia=sys.executable, java=sys.executable, jar='unused'))
        case = dict(dataset='toy', minsup='0.5', input_path=str(input_path),
                    n_transactions=2, input_sha256=c.inspect_input(input_path)['sha256'])

        def fake_command(variant, **kw):
            text = '2 1 #SUP: 1\n1 #SUP: 2\n' if variant == 'spmf' else '1 #SUP: 2\n1 2 #SUP: 1\n'
            return [sys.executable, '-I', '-c',
                    'import pathlib,sys; pathlib.Path(sys.argv[1]).write_bytes(sys.argv[2].encode())',
                    str(kw['output_path']), text]

        with patch.object(c, 'build_command', side_effect=fake_command):
            evidence = c.run_condition(work, meta, case, scope='pilot', repetitions=1)
        self.assertTrue(evidence['equal'])
        self.assertEqual(evidence['count'], 2)
        rows = c.read_measurements(work / 'runs.csv')
        self.assertEqual(len(rows), 2)
        for row in rows:
            run = work / 'attempts' / row['attempt_id']
            self.assertTrue((run / 'measurement.json').exists())
            self.assertTrue((run / 'validation.json').exists())
            self.assertFalse((run / 'output.txt').exists())
            self.assertTrue((run / 'stdout.log').exists())
        with patch.object(c, 'build_command', side_effect=fake_command):
            resumed = c.run_condition(work, meta, case, scope='pilot', repetitions=1)
        self.assertTrue(resumed['equal'])
        self.assertEqual(len(c.read_measurements(work / 'runs.csv')), 2)


if __name__ == '__main__':
    unittest.main()
