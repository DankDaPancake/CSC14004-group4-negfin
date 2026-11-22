"""Real Windows child tests, including short-lived process working-set peak."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    'spmf_process', Path(__file__).resolve().parents[1] / 'spmf_process.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


@unittest.skipUnless(os.name == 'nt', 'Windows native RSS implementation')
class ProcessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='runner space ')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.directory = self.root / 'run with spaces'

    def run_child(self, code, **limits):
        options = dict(timeout_seconds=3, output_cap_bytes=1024 * 1024,
                       rss_cap_bytes=512 * 1024 * 1024, poll_seconds=0.01)
        options.update(limits)
        # Output path is an argv element, never shell interpolated.
        return p.run_process([sys.executable, '-I', '-c', code,
                              str(self.directory / 'output.txt')],
                             self.directory, **options)

    def test_success_output_logs_and_wall_time(self):
        r = self.run_child("import pathlib,sys,time; print('hello'); "
                           "time.sleep(.08); pathlib.Path(sys.argv[1]).write_bytes(b'abc')")
        self.assertEqual(r['status'], 'ok')
        self.assertEqual(r['exit_code'], 0)
        self.assertEqual(r['output_bytes'], 3)
        self.assertGreaterEqual(r['process_wall_seconds'], .08)
        self.assertGreater(r['maxrss_bytes'], 0)
        self.assertIn('PeakWorkingSetSize', r['rss_method'])
        self.assertIn('hello', (self.directory / 'stdout.log').read_text())
        wall = r['process_wall_seconds']
        time.sleep(.05)  # Validation/reporting after return cannot change wall.
        self.assertEqual(r['process_wall_seconds'], wall)

    def test_error_retains_stderr_and_exit(self):
        r = self.run_child("import sys; print('bad',file=sys.stderr); sys.exit(7)")
        self.assertEqual(r['status'], 'error')
        self.assertEqual(r['exit_code'], 7)
        self.assertIn('bad', (self.directory / 'stderr.log').read_text())

    def test_immediate_exit_preserves_native_peak(self):
        r = self.run_child("import pathlib,sys; data=bytearray(32*1024*1024); "
                           "pathlib.Path(sys.argv[1]).write_bytes(b'x')", poll_seconds=.5)
        self.assertEqual(r['status'], 'ok')
        self.assertGreaterEqual(r['maxrss_bytes'], 32 * 1024 * 1024)
        self.assertLess(r['process_wall_seconds'], 2)

    def test_timeout_terminates_and_waits(self):
        r = self.run_child('import time; time.sleep(20)', timeout_seconds=.1)
        self.assertEqual(r['status'], 'timeout')
        self.assertNotEqual(r['exit_code'], 0)
        self.assertLess(r['process_wall_seconds'], 3)

    def test_output_cap_while_running(self):
        r = self.run_child("import pathlib,sys,time; "
                           "pathlib.Path(sys.argv[1]).write_bytes(b'x'*200); time.sleep(20)",
                           output_cap_bytes=100)
        self.assertEqual(r['status'], 'output_cap')
        self.assertEqual(r['output_bytes'], 200)

    def test_output_cap_after_fast_exit(self):
        r = self.run_child("import pathlib,sys; pathlib.Path(sys.argv[1]).write_bytes(b'x'*200)",
                           output_cap_bytes=100, poll_seconds=.5)
        self.assertEqual(r['status'], 'output_cap')

    def test_staged_julia_files_count_toward_cap(self):
        r = self.run_child("import pathlib,sys,time; "
                           "pathlib.Path(sys.argv[1]).with_name('jl_pending').write_bytes(b'x'*200); "
                           "time.sleep(20)", output_cap_bytes=100)
        self.assertEqual(r['status'], 'output_cap')
        self.assertTrue((self.directory / 'jl_pending').exists())

    def test_memory_cap_on_live_and_exited_child(self):
        for delay in ('; import time; time.sleep(20)', ''):
            self.directory = self.root / ('memory' + str(len(delay)))
            r = self.run_child('data=bytearray(32*1024*1024)' + delay,
                               rss_cap_bytes=20 * 1024 * 1024, poll_seconds=.1)
            self.assertEqual(r['status'], 'memory_cap')
            self.assertGreater(r['maxrss_bytes'], 20 * 1024 * 1024)

    def test_missing_output_is_not_success(self):
        r = self.run_child('pass')
        self.assertEqual(r['status'], 'error')

    def test_missing_executable_retains_launch_failure(self):
        r = p.run_process([str(self.root / 'missing.exe')], self.directory,
                          timeout_seconds=1, output_cap_bytes=100, rss_cap_bytes=100)
        self.assertEqual(r['status'], 'error')
        self.assertIsNone(r['exit_code'])
        self.assertIn('launch_error', r)

    def test_existing_directory_never_reuses_stale_output(self):
        self.directory.mkdir()
        stale = self.directory / 'output.txt'
        stale.write_bytes(b'keep')
        with self.assertRaises(FileExistsError):
            self.run_child('pass')
        self.assertEqual(stale.read_bytes(), b'keep')

    def test_output_scan_tolerates_atomic_rename_between_listing_and_stat(self):
        class VanishedFile:
            name = 'jl_pending'
            def is_file(self):
                return True
            def stat(self):
                raise FileNotFoundError('renamed by child')
        with patch.object(Path, 'iterdir', return_value=iter([VanishedFile()])):
            self.assertEqual(p._output_bytes(self.root), 0)

    def test_disk_and_invalid_limits(self):
        free = p.available_disk_bytes(self.root)
        self.assertGreater(free, 0)
        with self.assertRaisesRegex(ValueError, 'disk'):
            p.require_disk(self.root, free + 1024 * 1024 * 1024)
        with self.assertRaises(ValueError):
            self.run_child('pass', poll_seconds=0)
        self.assertFalse(self.directory.exists())


if __name__ == '__main__':
    unittest.main()
