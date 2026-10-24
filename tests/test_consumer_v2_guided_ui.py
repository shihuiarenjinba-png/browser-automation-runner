"""Guardrails for the consumer v2 guided UI, without a display server."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
class ConsumerV2GuidedUiTests(unittest.TestCase):
    def test_beginner_workflow_visible_first(self):
        code = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn('self.notebook.add(self.guide_tab', code)
        self.assertIn('self.notebook.add(self.step_tab', code)
        self.assertIn('self.notebook.add(self.advanced_tab, text=self.t("③ 確認して実行"', code)
        self.assertIn('試運転で操作内容を確認', code)
        self.assertNotIn("Start here: 1. Choose workflow JSON", code)

    def test_no_unsafe_live_shortcut(self):
        code = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn('self._live_running', code)
        self.assertIn('messagebox.askyesno', code)
        self.assertIn('self.preview_revision', code)

if __name__ == "__main__":
    unittest.main()
