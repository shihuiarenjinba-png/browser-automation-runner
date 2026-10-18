"""Dry-run approval must match the exact browser workflow and is single-use."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from desktop_app import BrowserAutomationDesktop


class BrowserPreviewGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "browser.json"
        self.workflow = {
            "root_dir": self.tmp.name,
            "allow_hosts": ["example.com"],
            "steps": [{"action": "goto", "url": "https://example.com"}],
        }
        self.path.write_text(json.dumps(self.workflow), encoding="utf-8")
        app = BrowserAutomationDesktop.__new__(BrowserAutomationDesktop)
        app.lang = "ja"
        app.root = None
        app.config_path = Mock()
        app.config_path.get.return_value = str(self.path)
        app.config = self.workflow
        app.preview_revision = None
        app._live_running = False
        app._load_config = Mock(return_value=True)
        app._append = Mock()
        app.dry_btn = Mock()
        app.run_btn = Mock()
        app.status = Mock()
        self.app = app

    def test_live_refused_before_dry_run(self):
        with patch("desktop_app.messagebox.showwarning") as warning, \
             patch("desktop_app.threading.Thread") as thread:
            self.app._run_live()
        warning.assert_called_once()
        thread.assert_not_called()

    def test_dry_run_authorizes_current_workflow_only(self):
        self.app._dry_run()
        approved = self.app.preview_revision
        self.assertEqual(approved, self.app._revision(self.workflow))
        self.assertIsNotNone(approved)
        self.workflow["steps"][0]["url"] = "https://example.com/changed"
        with patch("desktop_app.messagebox.showwarning") as warning, \
             patch("desktop_app.threading.Thread") as thread:
            self.app._run_live()
        warning.assert_called_once()
        thread.assert_not_called()

    def test_approval_consumed_before_worker_starts(self):
        self.app._dry_run()
        with patch("desktop_app.messagebox.askyesno", return_value=True), \
             patch("desktop_app.threading.Thread") as thread:
            self.app._run_live()
            thread.return_value.start.assert_called_once()
        self.assertIsNone(self.app.preview_revision)
        self.assertTrue(self.app._live_running)

    def test_cancelling_confirmation_preserves_dry_run(self):
        self.app._dry_run()
        approved = self.app.preview_revision
        with patch("desktop_app.messagebox.askyesno", return_value=False), \
             patch("desktop_app.threading.Thread") as thread:
            self.app._run_live()
        thread.assert_not_called()
        self.assertEqual(self.app.preview_revision, approved)

    def test_switching_config_path_revokes_approval(self):
        self.app._dry_run()
        alternate = self.path.with_name("other.json")
        alternate.write_text(json.dumps(self.workflow), encoding="utf-8")
        self.app.config_path.get.return_value = str(alternate)
        with patch("desktop_app.messagebox.showwarning") as warning:
            self.app._run_live()
        warning.assert_called_once()


if __name__ == "__main__":
    unittest.main()
