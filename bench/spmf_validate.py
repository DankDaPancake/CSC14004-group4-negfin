"""Bounded-payload external canonicalization of SPMF itemset output.

Chunk budget counts encoded record bytes, not Python object overhead. Canonical
files are sorted by numeric item tuple, independent of miner enumeration order.
"""
from contextlib import ExitStack
import hashlib
import heapq
from pathlib import Path
import re
import tempfile

_RECORD = re.compile(r'^\s*(.*?)\s*#SUP:\s*([0-9]+)\s*$')


def parse_record(line: str, *, min_count: int, n_transactions: int):
    text = line.strip()
    if not text or (text[0] in '@%#' and not text.startswith('#SUP:')):
        return None
    if not line.endswith('\n'):
        raise ValueError('Truncated record (missing newline)')
    match = _RECORD.fullmatch(text)
    if not match:
        raise ValueError('Invalid itemset/support record')
    tokens = match[1].split()
    if not tokens or any(not re.fullmatch(r'[0-9]+', x) for x in tokens):
        raise ValueError('Invalid items')
    items = tuple(sorted(int(x) for x in tokens))
    if items[0] <= 0 or len(set(items)) != len(items):
        raise ValueError('Items must be positive and distinct')
    support = int(match[2])
    if not max(1, min_count) <= support <= n_transactions:
        raise ValueError('Support outside expected threshold/transaction range')
    return items, support


def _encode(record):
    items, support = record
    return (f'{" ".join(map(str, items))} #SUP: {support}\n').encode('ascii')


def _records(handle):
    for line in handle:
        items, support = line.rstrip('\n').split(' #SUP: ')
        yield tuple(map(int, items.split())), int(support)


def _sha256(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def canonicalize(source: Path, destination: Path, scratch: Path, *, min_count: int,
                 n_transactions: int, chunk_bytes: int = 67108864,
                 fan_in: int = 32, scratch_cap_bytes: int = 17179869184) -> dict:
    source, destination, scratch = map(Path, (source, destination, scratch))
    if chunk_bytes <= 0 or fan_in < 2 or scratch_cap_bytes <= 0:
        raise ValueError('Invalid chunk/fan-in/scratch limits')
    if not 0 <= min_count <= n_transactions:
        raise ValueError('Invalid support bounds')
    if destination.exists():
        raise FileExistsError(destination)
    scratch.mkdir(parents=True, exist_ok=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Per-call subdirectory means cleanup cannot remove another run's scratch.
    with tempfile.TemporaryDirectory(prefix='canonical-', dir=scratch) as directory:
        work = Path(directory)
        sizes = {}
        live_bytes = 0
        serial = 0

        def fresh():
            nonlocal serial
            serial += 1
            return work / f'{serial:08d}.txt'

        def write_records(path, records):
            nonlocal live_bytes
            previous = None
            count = 0
            sizes[path] = 0
            with path.open('xb') as handle:
                for record in records:
                    if record[0] == previous:
                        raise ValueError(f'Duplicate itemset: {record[0]}')
                    previous = record[0]
                    data = _encode(record)
                    if live_bytes + len(data) > scratch_cap_bytes:
                        raise ValueError('Validation scratch cap exceeded')
                    handle.write(data)
                    sizes[path] += len(data)
                    live_bytes += len(data)
                    count += 1
            return count

        def remove(path):
            nonlocal live_bytes
            path.unlink()
            live_bytes -= sizes.pop(path)

        chunks = []
        batch = []
        payload = 0
        with source.open('r', encoding='utf-8-sig', newline=None) as handle:
            for number, line in enumerate(handle, 1):
                try:
                    record = parse_record(line, min_count=min_count,
                                          n_transactions=n_transactions)
                except ValueError as exc:
                    raise ValueError(f'{source}:{number}: {exc}') from exc
                if record is None:
                    continue
                batch.append(record)
                payload += len(line.encode('utf-8'))
                if payload >= chunk_bytes:
                    path = fresh()
                    write_records(path, sorted(batch))
                    chunks.append(path)
                    batch, payload = [], 0
        if batch or not chunks:
            path = fresh()
            write_records(path, sorted(batch))
            chunks.append(path)
        while len(chunks) > 1:
            following = []
            for start in range(0, len(chunks), fan_in):
                group = chunks[start:start + fan_in]
                if len(group) == 1:
                    following.extend(group)
                    continue
                path = fresh()
                with ExitStack() as stack:
                    streams = [_records(stack.enter_context(p.open('r', encoding='ascii')))
                               for p in group]
                    write_records(path, heapq.merge(*streams))
                following.append(path)
                for old in group:
                    remove(old)
            chunks = following
        canonical = chunks[0]
        count = 0
        # A final pass also validates duplicates in the single-chunk case.
        with canonical.open('rb') as handle:
            for _ in handle:
                count += 1
        result = dict(count=count, canonical_sha256=_sha256(canonical),
                      source_sha256=_sha256(source))
        # Exclusive create protects races as well as the initial exists check.
        created = False
        try:
            with destination.open('xb') as output:
                created = True
                with canonical.open('rb') as incoming:
                    while data := incoming.read(1024 * 1024):
                        if live_bytes + len(data) > scratch_cap_bytes:
                            raise ValueError('Validation scratch cap exceeded')
                        output.write(data)
                        live_bytes += len(data)
        except BaseException:
            if created:
                destination.unlink(missing_ok=True)
            raise
        return result


def compare_canonical(left: Path, right: Path) -> dict:
    """Compare actual (left) to reference (right), including differing supports."""
    missing = extra = support_mismatch = 0
    with Path(left).open('r', encoding='ascii') as a, Path(right).open('r', encoding='ascii') as b:
        actual, reference = _records(a), _records(b)
        x, y = next(actual, None), next(reference, None)
        while x is not None or y is not None:
            if y is None or (x is not None and x[0] < y[0]):
                extra += 1
                x = next(actual, None)
            elif x is None or y[0] < x[0]:
                missing += 1
                y = next(reference, None)
            else:
                support_mismatch += x[1] != y[1]
                x, y = next(actual, None), next(reference, None)
    return dict(missing=missing, extra=extra, support_mismatch=support_mismatch,
                equal=(missing == extra == support_mismatch == 0))
