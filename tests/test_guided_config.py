"""Guided first-run forms: no network, no Tk display, no existing config edits."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from guided_config import GuidedConfigError, https_host, save_new_config

from guided_config import make_screenshot_workflow
from desktop_app import BrowserAutomationDesktop


class GuidedBrowserSetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def make(self, **overrides):
        data = {"root_dir": str(self.root),
                "url": "https://example.com/", "filename": "page.png"}
        return make_screenshot_workflow(**{**data, **overrides})

    def test_first_run_only_goto_and_screenshot_never_overwrites(self):
        data = self.make()
        self.assertEqual([x["action"] for x in data["steps"]], ["goto", "screenshot"])
        self.assertEqual(data["steps"][-1]["overwrite"], False)
        self.assertEqual(data["steps"][-1]["path"], "screenshots/page.png")
        self.assertEqual(data["resource_hosts"], [])
        self.assertTrue(data["headless"])

    def test_reject_invalid_urls_and_local_hosts(self):
        for url in ("http://example.com", "https://user:p@example.com/",
                    "https://localhost", "https://127.0.0.1",
                    "https://192.168.0.1/", "https://example.com:81",
                    "https://example.com/#fragment", "https://example.com/?api_key=secret", "https://bad host/"):
            with self.subTest(url=url), self.assertRaises(GuidedConfigError):
                https_host(url)

    def test_screenshot_filename_cannot_escape_or_use_reserved_names(self):
        for name in ("../out.png", "sub/capture.png", "C:drive.png",
                     "con.png", "page.jpg", "hidden/.png", ".png"):
            with self.subTest(name=name), self.assertRaises(GuidedConfigError):
                self.make(filename=name)

    def test_saved_json_can_be_validated_without_browser_launch(self):
        from browser_runner import BrowserRunner
        file = self.root / "new.json"
        save_new_config(file, self.make())
        config = json.loads(file.read_text(encoding="utf-8"))
        with patch("browser_runner.sync_playwright") as playwright:
            BrowserRunner(config, dry_run=True).run()
        playwright.assert_not_called()
        self.assertFalse((self.root / "screenshots").exists())

    def test_empty_or_missing_folder_must_be_chosen_explicitly(self):
        with self.assertRaises(GuidedConfigError):
            self.make(root_dir="")
        with self.assertRaises(GuidedConfigError):
            self.make(root_dir=str(self.root / "missing-folder"))

    def test_existing_json_is_never_replaced(self):
        file = self.root / "existing.json"
        file.write_text("precious customer config", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            save_new_config(file, self.make())
        self.assertEqual(file.read_text(encoding="utf-8"), "precious customer config")

    def test_gui_wizard_only_saves_config(self):
        app = BrowserAutomationDesktop.__new__(BrowserAutomationDesktop)
        app._live_running = False
        app.lang = "ja"
        app.root = None
        app.t = lambda ja,en: ja
        app.guide_root = Mock(get=Mock(return_value=str(self.root)))
        app.guide_url = Mock(get=Mock(return_value="https://example.com/"))
        app.guide_output = Mock(get=Mock(return_value="fresh.png"))
        app.config_path = Mock()
        app.notebook = Mock()
        app.advanced_tab = "advanced"
        app._load_config = Mock(return_value=True)
        app.status = Mock()
        app.preview_revision = "old approval"
        file = self.root / "wizard.json"
        with patch("desktop_app.filedialog.asksaveasfilename", return_value=str(file)), \
             patch("desktop_app.sync_playwright", create=True) as playwright:
            app._create_guided_config()
            playwright.assert_not_called()
        self.assertEqual(json.loads(file.read_text(encoding="utf-8"))["steps"][1]["path"],
                         "screenshots/fresh.png")
        self.assertIsNone(app.preview_revision)
        app._load_config.assert_called_once_with(True)


if __name__ == "__main__":
    unittest.main()
