"""Consumer browser onboarding must be folder-picker driven."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ConsumerBrowserPickerTests(unittest.TestCase):
    def test_output_folder_uses_windows_picker(self):
        code = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn('state="readonly" if i == 0 else "normal"', code)
        self.assertIn('command=self._choose_guide_root', code)
        self.assertIn("self.guide_root.set(name)\n            self.preview_revision = None", code)

    def test_first_screen_is_not_json_first(self):
        code = (ROOT / "desktop_app.py").read_text(encoding="utf-8")
        self.assertIn("設定を保存します", code)
        self.assertIn("保存した設定を開く", code)
        self.assertNotIn("② JSONとして新規保存", code)
        self.assertIn("messagebox.askyesno", code)

if __name__ == "__main__":
    unittest.main()
