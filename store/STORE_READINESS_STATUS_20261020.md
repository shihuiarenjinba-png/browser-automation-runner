# Store readiness status — 2026-10-20

**DRAFT / NOT READY FOR SUBMISSION**

Validated source head: `81c1893ed529d6434ba590639847817e91a7305e`.

## Verified

- Local code tests: 40 passed; 22 subtests passed.
- Fresh unsigned MSIX build/round-trip: PASS; SHA256 `7f4b07befa776b9daafbbd42a5db56981da307b740b8afe5e4a6e4dc91e43419`.
- Local-validation signed copy SHA256 `5c69ae75bfc329164cefb867f238579115db5ba05495b1de50e5a3173e6fe5cc`; signer matched thumbprint `60BB363D9BE876439137DFB31247952463106BDD`.
- Windows API calculated PFN `OkinawaDesktopTools.BrowserAutomationRunner_j8yefg9jgfh58`, matching the captured draft.
- Bundled provenance: Playwright Python 1.62.0; Chrome for Testing and Headless Shell 151.0.7922.34, revision 1234. Source-payload and round-tripped `chrome.exe` hashes match.

## CI

Current-head runs `39400015925` and `39400015993` are **CI_FAIL_UNDIAGNOSED**. Build and Ubuntu/Windows reliability jobs failed before runner assignment; `steps=[]`; no job-log blob exists. The root cause has not been established.

## Not yet verified

MSIX installation, Start-menu launch, installed JP/EN UI, restart, bundled-browser launch/local safe workflow, Store screenshots, WACK, and live Partner Center identity are NOT TESTED. Customer-visible Playwright notices, final-package SBOM, and owner/legal redistribution approval are still required. No certificate-store change is authorized.

## Submission safeguards

- Microsoft Standard Application License Terms (SALT) are the default when **Additional license terms** is left blank. A custom EULA is not an engineering prerequisite unless the owner chooses different terms.
- Prices and Japan/United States markets remain proposals only. Disable future-market automatic expansion.
- Immediately before certification submission, select **Don't publish this submission until I select Publish now**. The default can publish automatically after certification.
- AI-generated icons remain unapproved concepts and are not package or Store assets.
- Certificate-store changes, Store upload/submission/publication, and main/release merges remain unauthorized.
