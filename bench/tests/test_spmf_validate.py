"""Real-file tests: ordering, malformed records and bounded external merge."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'spmf_validate.py'
spec = importlib.util.spec_from_file_location('spmf_validate', MODULE)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def canonical(self, name, text, **kwargs):
        src = self.root / (name + '.txt')
        src.write_bytes(text.encode('utf-8'))
        dst = self.root / (name + '.canonical')
        result = v.canonicalize(src, dst, self.root / (name + '.scratch'),
                                min_count=2, n_transactions=4, **kwargs)
        return dst, result

    def test_order_independent_equality_and_digest(self):
        left, a = self.canonical('a', '2 1 #SUP: 3\n4 #SUP: 2\n')
        right, b = self.canonical('b', '4 #SUP: 2\n1 2 #SUP: 3\n')
        expected = b'1 2 #SUP: 3\n4 #SUP: 2\n'
        self.assertEqual(left.read_bytes(), expected)
        self.assertEqual(a['canonical_sha256'], hashlib.sha256(expected).hexdigest())
        self.assertEqual(a['canonical_sha256'], b['canonical_sha256'])
        self.assertEqual(a['count'], 2)
        self.assertEqual(a['source_sha256'], hashlib.sha256(b'2 1 #SUP: 3\n4 #SUP: 2\n').hexdigest())
        self.assertEqual(v.compare_canonical(left, right),
                         dict(missing=0, extra=0, support_mismatch=0, equal=True))

    def test_missing_extra_and_support_mismatch(self):
        actual, _ = self.canonical('a', '1 #SUP: 2\n2 #SUP: 3\n')
        reference, _ = self.canonical('b', '2 #SUP: 4\n3 #SUP: 2\n')
        self.assertEqual(v.compare_canonical(actual, reference),
                         dict(missing=1, extra=1, support_mismatch=1, equal=False))

    def test_parser_rejects_invalid_records(self):
        for line in ('#SUP: 3\n', '0 #SUP: 3\n', '-1 #SUP: 3\n',
                     '1 1 #SUP: 3\n', 'x #SUP: 3\n', '1 #SUP: 0\n',
                     '1 #SUP: 1\n', '1 #SUP: 5\n', '1 #SUP: 2.0\n',
                     '1 #SUP:', '1 #SUP: 3', '1 #SUP: 3 junk\n'):
            with self.subTest(line=line), self.assertRaises(ValueError):
                v.parse_record(line, min_count=2, n_transactions=4)

    def test_parser_allows_comments_and_normalizes(self):
        for line in ('\n', '@ITEM=1=A\n', '% comment\n', '# comment\n'):
            self.assertIsNone(v.parse_record(line, min_count=2, n_transactions=4))
        self.assertEqual(v.parse_record(' 2 1 #SUP: 3\r\n', min_count=2,
                                        n_transactions=4), ((1, 2), 3))

    def test_duplicate_itemsets_across_chunks_different_support(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.canonical('a', '1 2 #SUP: 2\n3 #SUP: 3\n2 1 #SUP: 4\n',
                           chunk_bytes=1, fan_in=2)
        self.assertFalse((self.root / 'a.canonical').exists())
        self.assertTrue((self.root / 'a.txt').exists())

    def test_many_merge_passes_numeric_order(self):
        text = ''.join(f'{i} #SUP: 2\n' for i in range(25, 0, -1))
        dst, result = self.canonical('a', text, chunk_bytes=1, fan_in=2)
        self.assertEqual(dst.read_text(), ''.join(f'{i} #SUP: 2\n' for i in range(1, 26)))
        self.assertEqual(result['count'], 25)
        self.assertEqual(list((self.root / 'a.scratch').iterdir()), [])

    def test_scratch_cap_cleans_only_owned_files(self):
        scratch = self.root / 'a.scratch'
        scratch.mkdir()
        sentinel = scratch / 'keep.txt'
        sentinel.write_text('keep')
        with self.assertRaisesRegex(ValueError, 'scratch'):
            self.canonical('a', '1 #SUP: 2\n2 #SUP: 2\n', scratch_cap_bytes=5)
        self.assertEqual(sentinel.read_text(), 'keep')
        self.assertEqual(list(scratch.iterdir()), [sentinel])
        self.assertFalse((self.root / 'a.canonical').exists())

    def test_existing_destination_is_not_overwritten(self):
        dst = self.root / 'a.canonical'
        dst.write_text('keep')
        with self.assertRaises(FileExistsError):
            self.canonical('a', '1 #SUP: 2\n')
        self.assertEqual(dst.read_text(), 'keep')

    def test_empty_output_is_valid(self):
        dst, result = self.canonical('a', '')
        self.assertEqual(result['count'], 0)
        self.assertEqual(dst.read_bytes(), b'')

    def test_invalid_limits_fail_without_output(self):
        for kwargs in ({'chunk_bytes': 0}, {'fan_in': 1}, {'scratch_cap_bytes': 0}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.canonical('invalid', '1 #SUP: 2\n', **kwargs)


if __name__ == '__main__':
    unittest.main()
