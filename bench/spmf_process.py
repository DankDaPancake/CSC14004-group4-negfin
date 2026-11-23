"""Windows process wall/peak-working-set measurement, without shell commands.

RSS/output limits are monitored guards with possible between-poll overshoot,
not hard OS quotas. The native process handle stays alive through final metrics.
"""
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import subprocess
import time


class _Counters(ctypes.Structure):
    _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
        (name, ctypes.c_size_t) for name in (
            'PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage',
            'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
            'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]


def _windows_api():
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.DuplicateHandle.argtypes = [wintypes.HANDLE, wintypes.HANDLE,
        wintypes.HANDLE, ctypes.POINTER(wintypes.HANDLE), wintypes.DWORD,
        wintypes.BOOL, wintypes.DWORD]
    kernel.DuplicateHandle.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE,
        ctypes.POINTER(_Counters), wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    return kernel, psapi


def _peak(psapi, handle):
    counters = _Counters()
    counters.cb = ctypes.sizeof(counters)
    if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return counters.PeakWorkingSetSize


def available_disk_bytes(path: Path) -> int:
    return shutil.disk_usage(path).free


def require_disk(path: Path, minimum: int) -> None:
    if available_disk_bytes(path) < minimum:
        raise ValueError(f'disk_limit: need at least {minimum} free bytes at {path}')


def _output_bytes(directory):
    total = 0
    for path in directory.iterdir():
        if path.name != 'output.txt' and not path.name.startswith('jl_'):
            continue
        try:
            if path.is_file():
                total += path.stat().st_size
        except FileNotFoundError:
            # Julia atomically renames staged output. A vanished entry is
            # checked at the next poll and output is checked again after exit.
            continue
    return total


def run_process(argv: list[str], directory: Path, *, timeout_seconds: float,
                output_cap_bytes: int, rss_cap_bytes: int, poll_seconds: float = 0.02,
                env: dict[str, str] | None = None) -> dict:
    if os.name != 'nt':
        raise RuntimeError('Native peak RSS measurement currently requires Windows')
    if not argv or min(timeout_seconds, output_cap_bytes, rss_cap_bytes, poll_seconds) <= 0:
        raise ValueError('Process limits and poll interval must be positive')
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    kernel, psapi = _windows_api()
    result = dict(status='ok', exit_code=None, argv=list(argv),
                  started_at=datetime.now(timezone.utc).isoformat(),
                  rss_method='Windows GetProcessMemoryInfo.PeakWorkingSetSize',
                  poll_seconds=poll_seconds, maxrss_bytes=0, output_bytes=0)
    child = None
    retained = wintypes.HANDLE()
    started = None
    wall = 0.0
    try:
        with (directory / 'stdout.log').open('xb') as stdout, \
             (directory / 'stderr.log').open('xb') as stderr:
            started = time.perf_counter()
            try:
                # CPython's Windows Popen retains the full-access CreateProcess
                # handle. Duplicate it before poll()/wait(), whose lifetime is
                # independent of our final peak-memory query.
                child = subprocess.Popen(argv, stdout=stdout, stderr=stderr,
                                         stdin=subprocess.DEVNULL, env=env)
            except OSError as exc:
                wall = time.perf_counter() - started
                result.update(status='error', launch_error=str(exc))
                return result | dict(process_wall_seconds=wall,
                    finished_at=datetime.now(timezone.utc).isoformat())
            current = kernel.GetCurrentProcess()
            if not kernel.DuplicateHandle(current, wintypes.HANDLE(int(child._handle)),
                                          current, ctypes.byref(retained), 0, False, 2):
                raise ctypes.WinError(ctypes.get_last_error())
            while True:
                # OS event wait returns immediately for an already-exited child.
                # No sleep-poll quantization is added after prompt exits.
                wait_ms = max(1, int(min(poll_seconds,
                    max(0.001, timeout_seconds - (time.perf_counter() - started))) * 1000))
                signal = kernel.WaitForSingleObject(retained, wait_ms)
                elapsed = time.perf_counter() - started
                if signal == 0:
                    wall = elapsed  # Stop before file scans and final validation.
                    break
                if signal != 258:
                    raise ctypes.WinError(ctypes.get_last_error())
                result['maxrss_bytes'] = max(result['maxrss_bytes'], _peak(psapi, retained))
                if elapsed > timeout_seconds:
                    result['status'] = 'timeout'
                elif _output_bytes(directory) > output_cap_bytes:
                    result['status'] = 'output_cap'
                elif result['maxrss_bytes'] > rss_cap_bytes:
                    result['status'] = 'memory_cap'
                if result['status'] != 'ok':
                    child.kill()
                    child.wait()
                    wall = time.perf_counter() - started
                    break
            child.wait()
            result['exit_code'] = child.returncode
            result['maxrss_bytes'] = max(result['maxrss_bytes'], _peak(psapi, retained))
            result['output_bytes'] = _output_bytes(directory)
            if result['status'] == 'ok':
                if result['output_bytes'] > output_cap_bytes:
                    result['status'] = 'output_cap'
                elif result['maxrss_bytes'] > rss_cap_bytes:
                    result['status'] = 'memory_cap'
                elif wall > timeout_seconds:
                    result['status'] = 'timeout'
                elif child.returncode != 0 or not (directory / 'output.txt').is_file():
                    result['status'] = 'error'
    finally:
        if child is not None:
            if child.poll() is None:
                child.kill()
                child.wait()
            # Popen has no public close-process-handle API on Windows. The
            # retained duplicate has already served its purpose at this point.
            child._handle.Close()
        if retained:
            kernel.CloseHandle(retained)
    result['process_wall_seconds'] = wall
    result['finished_at'] = datetime.now(timezone.utc).isoformat()
    return result
