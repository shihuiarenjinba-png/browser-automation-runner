from __future__ import annotations

import ast
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import ui_language

ROOT = Path(__file__).resolve().parents[1]


class LanguageUITests(unittest.TestCase):
    def test_ui_sources_parse(self) -> None:
        for relative in ("desktop_app.py", "ui_language.py"):
            path = ROOT / relative
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def test_language_and_advanced_warning_contract(self) -> None:
        source = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("言語 / Language", source)
        self.assertIn('("日本語", "English")', source)
        self.assertIn("Advanced browser execution", source)
        self.assertIn("APIで代替できない", source)
        self.assertIn("No browser actions executed", source)

    def test_language_setting_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"LOCALAPPDATA": tmp, "PRIVATE_AUTOMATION_UI_LANGUAGE": ""}, clear=False):
            ui_language.save_language("test-browser", "en")
            self.assertEqual(ui_language.load_language("test-browser"), "en")
            ui_language.save_language("test-browser", "ja")
            self.assertEqual(ui_language.load_language("test-browser"), "ja")
            with self.assertRaises(ValueError):
                ui_language.save_language("test-browser", "fr")


if __name__ == "__main__":
    unittest.main()
