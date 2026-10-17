import hashlib
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('release_iso', Path(__file__).parents[1] / 'scripts/release-iso.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseAssemblyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.iso = self.root / 'test.iso'
        self.original = bytes(range(256)) * 19
        self.iso.write_bytes(self.original)
        self.iso.with_name('test.iso.sha256').write_text(hashlib.sha256(self.original).hexdigest() + '  test.iso\n')
        self.output = self.root / 'release'
        self.manifest = release.prepare(self.iso, self.output, chunk_size=1000)
        offset = 0
        for part in self.manifest['parts']:
            (self.output / part['file']).write_bytes(self.original[offset:offset + part['size']])
            offset += part['size']

    def join(self):
        return subprocess.run(['bash', str(self.output / 'JOIN-LINUX.sh')], capture_output=True)

    def test_roundtrip_exact_bytes_and_preserve_existing_iso(self):
        self.assertEqual(self.join().returncode, 0)
        self.assertEqual((self.output / 'test.iso').read_bytes(), self.original)
        self.assertNotEqual(self.join().returncode, 0)
        self.assertEqual((self.output / 'test.iso').read_bytes(), self.original)

    def test_corrupt_part_never_creates_iso(self):
        part = self.output / self.manifest['parts'][1]['file']
        part.write_bytes(b'x' * part.stat().st_size)
        self.assertNotEqual(self.join().returncode, 0)
        self.assertFalse((self.output / 'test.iso').exists())
        self.assertFalse((self.output / 'test.iso.partial').exists())

    def test_missing_part_never_creates_iso(self):
        (self.output / self.manifest['parts'][-1]['file']).unlink()
        self.assertNotEqual(self.join().returncode, 0)
        self.assertFalse((self.output / 'test.iso').exists())

    def test_reject_changed_original(self):
        self.iso.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            release.prepare(self.iso, self.output)
