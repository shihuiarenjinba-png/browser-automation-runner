import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "store"
NS = "http://schemas.microsoft.com/appx/manifest/foundation/windows10"
UAP10 = "http://schemas.microsoft.com/appx/manifest/uap/windows10/10"


class StoreIdentityDraftTests(unittest.TestCase):
    def test_identity_manifest_and_chromium_contract(self):
        identity=json.loads((STORE/"product_identity.json").read_text(encoding="utf-8"))
        self.assertEqual(identity["store_id"],"9NQHC8VW729G")
        self.assertEqual(identity["package_identity_name"],"OkinawaDesktopTools.BrowserAutomationRunner")
        self.assertEqual(identity["publisher"],"CN=46263F21-A700-41DB-8C9B-114C22FB82FC")
        self.assertIs(identity["submission_allowed"],False)
        self.assertEqual(identity["initial_msix_version"], "1.0.0.0")
        self.assertEqual(identity["legacy_initial_msix_version"], "0.1.0.0")
        self.assertEqual(identity["msix_package_version_status"], "TECHNICAL_DRAFT_ONLY_PUBLIC_RELEASE_HOLD")
        self.assertIs(identity["store_version_history_verified"], False)
        text=(STORE/"AppxManifest.template.xml").read_text(encoding="utf-8")
        for key,value in {"__PACKAGE_IDENTITY_NAME__":identity["package_identity_name"],"__PUBLISHER__":identity["publisher"],"__PUBLISHER_DISPLAY_NAME__":identity["publisher_display_name"],"__VERSION__":identity["initial_msix_version"]}.items(): text=text.replace(key,value)
        root=ET.fromstring(text); app=root.find(f".//{{{NS}}}Application")
        self.assertEqual(app.attrib["Executable"],"BrowserAutomationRunner.exe")
        self.assertEqual(app.attrib[f"{{{UAP10}}}RuntimeBehavior"],"packagedClassicApp")
        self.assertIsNotNone(root.find(".//{*}Capability[@Name='runFullTrust']"))
        builder=(STORE/"build_msix_draft.ps1").read_text(encoding="utf-8")
        self.assertIn('Join-Path $payload "pw-browsers"',builder)
        self.assertIn('bundled_chromium_roundtrip_verified=$true',builder)
        self.assertIn('third_party_rights_approved=$false',builder)
        self.assertIn('sale_approved=$false',builder)
        self.assertIn("Store MSIX version major component must be >= 1", builder)
        self.assertIn("store_version_history_verified", builder)
        workflow=(ROOT/".github"/"workflows"/"windows-desktop.yml").read_text(encoding="utf-8")
        self.assertIn("store/build_msix_draft.ps1",workflow)
        self.assertIn("BrowserAutomationRunner-Store-MSIX-UNSIGNED-DRAFT",workflow)
        self.assertIn("dist-validation/**",workflow)
        self.assertIn("source_commit=$sourceCommit", builder)
        self.assertIn("git -C $repoRoot rev-parse HEAD", builder)
        build_script=(ROOT/"build_windows.ps1").read_text(encoding="utf-8")
        self.assertIn("source_commit = $sourceCommit", build_script)
        self.assertIn("git -C $PSScriptRoot rev-parse HEAD", build_script)


if __name__ == "__main__": unittest.main()

