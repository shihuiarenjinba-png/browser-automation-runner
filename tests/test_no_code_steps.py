"""Offline tests for safe browser workflow configuration."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from guided_config import GuidedConfigError, save_new_config
from guided_steps import build_extra_step, build_nocode_workflow


class StepBuilderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def make(self, steps):
        return build_nocode_workflow(root_dir=str(self.root), url="https://example.com/",
                                     screenshot="capture.png", additional_steps=steps)

    def test_nocode_workflow_sequence(self):
        steps = [build_extra_step(action="fill", selector="#keyword", value="test"),
                 build_extra_step(action="click", selector="#send"),
                 build_extra_step(action="download", selector="#export", filename="export.csv")]
        config = self.make(steps)
        self.assertEqual([v["action"] for v in config["steps"]],
                         ["goto", "fill", "click", "download", "screenshot"])
        self.assertEqual(config["steps"][-2]["save_as"], "downloads/export.csv")
        self.assertFalse(config["steps"][-2]["overwrite"])

    def test_password_plaintext_and_unsafe_action_refused(self):
        with self.assertRaises(GuidedConfigError):
            build_extra_step(action="fill", selector="#password", value="secret")
        with self.assertRaises(GuidedConfigError):
            build_extra_step(action="evaluate", selector="body")
        self.assertEqual(build_extra_step(action="fill", selector="#password",
                         value="$"+"{ENV:MY_PASSWORD}")["action"], "fill")

    def test_unsafe_download_path_and_reserved_device_name_refused(self):
        for value in ("../secret.csv", "COM9.csv", "lpt1.txt", "a/b.csv"):
            with self.subTest(value=value), self.assertRaises(GuidedConfigError):
                build_extra_step(action="download", selector="#x", filename=value)
        with self.assertRaises(GuidedConfigError):
            self.make([{"action": "download", "selector": "#x",
                        "save_as": "../../secret.csv"}])

    def test_existing_json_not_replaced_and_dry_run_never_browses(self):
        config = self.make([build_extra_step(action="wait_for", selector=".ready")])
        with patch("browser_runner.sync_playwright") as playwright:
            from browser_runner import BrowserRunner
            BrowserRunner(config, dry_run=True).run()
            playwright.assert_not_called()
        file = self.root / "settings.json"
        save_new_config(file, config)
        with self.assertRaises(FileExistsError):
            save_new_config(file, config)


if __name__ == "__main__":
    unittest.main()
