import unittest
from pathlib import Path


class BrowserNoticeBundleContractTests(unittest.TestCase):
    def test_store_builder_collects_notices_and_verifies_inventory(self):
        root = Path(__file__).resolve().parents[1]
        builder = (root / "store" / "build_msix_draft.ps1").read_text(encoding="utf-8")
        self.assertIn("collect_browser_notices.py", builder)
        self.assertIn("PACKAGE_INVENTORY.json", builder)
        self.assertIn("third_party_notice_bundle_verified", builder)
        self.assertIn("package_inventory_verified", builder)

    def test_collector_requires_playwright_chromium_and_ffmpeg_notice_evidence(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "store" / "collect_browser_notices.py").read_text(encoding="utf-8")
        self.assertIn('distribution("playwright")', source)
        self.assertIn("Chromium/Chrome notice evidence was not found", source)
        self.assertIn("FFmpeg license evidence was not found", source)
        self.assertIn("browser-msix-package-inventory/1", source)


if __name__ == "__main__":
    unittest.main()
