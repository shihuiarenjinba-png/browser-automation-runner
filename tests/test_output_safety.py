import tempfile
import unittest
from pathlib import Path
from output_safety import save_capture, OutputSafetyError

class OutputTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'capture.png'
    def test_new(self):
        save_capture(self.path,lambda p:p.write_bytes(b'img'))
        self.assertEqual(self.path.read_bytes(),b'img')
    def test_collision_preserves_original(self):
        self.path.write_bytes(b'OLD')
        with self.assertRaises(OutputSafetyError):save_capture(self.path,lambda p:p.write_bytes(b'NEW'))
        self.assertEqual(self.path.read_bytes(),b'OLD')
    def test_explicit_overwrite(self):
        self.path.write_bytes(b'OLD')
        save_capture(self.path,lambda p:p.write_bytes(b'NEW'),overwrite=True)
        self.assertEqual(self.path.read_bytes(),b'NEW')
    def test_failure_no_file(self):
        def broken(p):p.write_bytes(b'partial');raise RuntimeError('download failed')
        with self.assertRaises(RuntimeError):save_capture(self.path,broken)
        self.assertFalse(self.path.exists())
    def test_failure_preserves_original(self):
        self.path.write_bytes(b'OLD')
        def broken(p):p.write_bytes(b'partial');raise RuntimeError('download failed')
        with self.assertRaises(RuntimeError):save_capture(self.path,broken,overwrite=True)
        self.assertEqual(self.path.read_bytes(),b'OLD')
    def test_empty_blocked(self):
        with self.assertRaises(OutputSafetyError):save_capture(self.path,lambda p:None)
        self.assertFalse(self.path.exists())
    def test_temp_cleanup(self):
        save_capture(self.path,lambda p:p.write_bytes(b'OK'))
        self.assertEqual(sorted(p.name for p in self.path.parent.iterdir()),['capture.png'])
    def test_directory_rejected(self):
        self.path.mkdir()
        with self.assertRaises(OutputSafetyError):save_capture(self.path,lambda p:p.write_bytes(b'X'))

if __name__=='__main__':unittest.main()
