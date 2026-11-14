import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

spec = importlib.util.spec_from_file_location('plot_benchmark', Path(__file__).with_name('plot-benchmark.py'))
plot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plot)


class RawAggregationTests(unittest.TestCase):
    def test_cli_requires_run_directory(self):
        result = subprocess.run([sys.executable, spec.origin], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('run_dir', result.stderr)

    def test_cold_median_and_range_excludes_other_scopes(self):
        rows = [dict(scope='cold', dataset='Chess', minsup='0.3', fraction='1.0',
                     emit_mode='cli', status='ok', process_wall_seconds=str(x)) for x in (4, 2, 3)]
        rows.append(dict(scope='warm', dataset='Chess', minsup='0.3', fraction='1.0',
                         emit_mode='count', status='ok', process_wall_seconds='999'))
        result = plot.aggregate_rows(rows, 'process_wall_seconds', scope='cold', emit_mode='cli')
        self.assertEqual(result[('Chess', '0.3', '1.0')], (3.0, 2.0, 4.0, 3))

    def test_failed_or_missing_measurements_are_rejected(self):
        base = dict(scope='cold', dataset='Chess', minsup='0.3', fraction='1.0', emit_mode='cli')
        for changes in (dict(status='timeout', process_wall_seconds='3'),
                        dict(status='ok', process_wall_seconds=''),
                        dict(status='ok', process_wall_seconds='NaN'),
                        dict(status='ok', process_wall_seconds='-1')):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                plot.aggregate_rows([base | changes], 'process_wall_seconds', scope='cold', emit_mode='cli')


if __name__ == '__main__':
    unittest.main()
