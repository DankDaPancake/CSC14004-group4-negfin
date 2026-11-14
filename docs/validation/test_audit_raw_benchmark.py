import csv
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('audit-raw-benchmark.py')


def write_csv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


class AuditTests(unittest.TestCase):
    def test_duplicate_phase_is_detected_even_with_five_rows(self):
        key = dict(run_id='r', variant='baseline', scope='warm', dataset='Chess', fraction='1.0',
                   minsup='0.5', emit_mode='count', repetition='1')
        run = dict(key, status='ok', phases_total_seconds='5', process_wall_seconds='', maxrss_bytes='')
        phases = [dict(key, phase=p, seconds='1', bytes='1', gc_seconds='0')
                  for p in ('normalize', 'prepare', 'build_bmc', 'mine', 'mine')]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_csv(root / 'runs.csv', [run])
            write_csv(root / 'phases.csv', phases)
            # Any summary is enough: the specific phase error must be reported.
            dims = {k: key[k] for k in ('variant', 'scope', 'dataset', 'fraction', 'minsup', 'emit_mode')}
            write_csv(root / 'summary.csv', [dict(dims, phase='', metric='phases_total_seconds',
                                                  median='5', min='5', max='5', n='1')])
            result = subprocess.run([sys.executable, str(SCRIPT), str(root)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('invalid phase names', result.stdout)


if __name__ == '__main__':
    unittest.main()
