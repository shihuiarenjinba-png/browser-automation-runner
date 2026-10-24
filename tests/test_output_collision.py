"""Filesystem safety regression tests; no real browser or remote requests."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from browser_runner import BrowserRunner, BrowserRunnerError


def make_runner(root: Path) -> BrowserRunner:
    return BrowserRunner({
        "root_dir": str(root),
        "allow_hosts": ["example.com"],
        "steps": [{"action": "goto", "url": "https://example.com"}],
    }, dry_run=True)


class MockScreenshotPage:
    def __init__(self, competitor: Path | None = None) -> None:
        self.competitor = competitor

    def screenshot(self, *, path: str, full_page: bool) -> None:
        Path(path).write_bytes(b"new image")
        if self.competitor is not None:
            self.competitor.write_bytes(b"competing writer")


class MockDownload:
    def __init__(self, competitor: Path | None = None) -> None:
        self.competitor = competitor

    def failure(self):
        return None

    def save_as(self, path: str) -> None:
        Path(path).write_bytes(b"new download")
        if self.competitor is not None:
            self.competitor.write_bytes(b"competing writer")


class DownloadInfo:
    def __init__(self, item) -> None:
        self.value = item

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class Locator:
    def click(self):
        pass


class MockDownloadPage:
    url = "https://example.com"

    def __init__(self, competitor: Path | None = None):
        self.download = MockDownload(competitor)

    def expect_download(self):
        return DownloadInfo(self.download)

    def locator(self, selector):
        return Locator()


class BrowserOutputSafetyTests(unittest.TestCase):
    def test_screenshot_creates_new_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runner = make_runner(root)
            runner._run_step(MockScreenshotPage(), {"action": "screenshot", "path": "snap.png"})
            self.assertEqual((root / "snap.png").read_bytes(), b"new image")

    def test_screenshot_collision_after_check_preserves_competitor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "snap.png"
            runner = make_runner(root)
            with self.assertRaisesRegex(BrowserRunnerError, "appeared during save"):
                runner._run_step(MockScreenshotPage(target), {"action": "screenshot", "path": "snap.png"})
            self.assertEqual(target.read_bytes(), b"competing writer")
            self.assertEqual(list(root.glob(".browser-shot-*")), [])

    def test_screenshot_overwrite_true_replaces_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "snap.png"
            target.write_bytes(b"old")
            make_runner(root)._run_step(MockScreenshotPage(), {
                "action": "screenshot", "path": "snap.png", "overwrite": True
            })
            self.assertEqual(target.read_bytes(), b"new image")

    def test_download_creates_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_runner(root)._run_step(MockDownloadPage(), {
                "action": "download", "selector": "#save", "save_as": "archive.bin"
            })
            self.assertEqual((root / "archive.bin").read_bytes(), b"new download")

    def test_download_collision_after_check_preserves_competitor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "archive.bin"
            with self.assertRaisesRegex(BrowserRunnerError, "appeared during save"):
                make_runner(root)._run_step(MockDownloadPage(target), {
                    "action": "download", "selector": "#save", "save_as": "archive.bin"
                })
            self.assertEqual(target.read_bytes(), b"competing writer")
            self.assertEqual(list(root.glob(".browser-download-*")), [])

    def test_download_overwrite_true_replaces_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "archive.bin"
            target.write_bytes(b"old")
            make_runner(root)._run_step(MockDownloadPage(), {
                "action": "download", "selector": "#save",
                "save_as": "archive.bin", "overwrite": True
            })
            self.assertEqual(target.read_bytes(), b"new download")

    def test_existing_file_without_overwrite_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "snap.png").write_bytes(b"original")
            with self.assertRaisesRegex(BrowserRunnerError, "overwrite=false"):
                make_runner(root)._run_step(MockScreenshotPage(), {
                    "action": "screenshot", "path": "snap.png"
                })
            self.assertEqual((root / "snap.png").read_bytes(), b"original")

    def test_download_outside_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(BrowserRunnerError, "outside root_dir"):
                make_runner(root)._validate_step({
                    "action": "download", "selector": "#save",
                    "save_as": "../outside.txt"
                })


if __name__ == "__main__":
    unittest.main()
