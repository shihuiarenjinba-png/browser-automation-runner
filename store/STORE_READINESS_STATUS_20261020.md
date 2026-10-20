# Store readiness status — 2026-10-20

**DRAFT / NOT READY FOR SUBMISSION**

Source head reviewed before this documentation commit: `81c1893ed529d6434ba590639847817e91a7305e`.

## Verified

- Code tests: 40 passed; 22 subtests passed locally.
- Fresh MSIX build/round-trip validation: PASS.
- Package hashes: unsigned 7f4b07befa776b9daafbbd42a5db56981da307b740b8afe5e4a6e4dc91e43419; local-validation signed 5c69ae75bfc329164cefb867f238579115db5ba05495b1de50e5a3173e6fe5cc.
- The local-validation signer matched the intended code-signing certificate thumbprint `60BB363D9BE876439137DFB31247952463106BDD`.

## Not yet verified

- Local signed MSIX installation.
- Launch from the Windows Start menu.
- Installed-package Japanese/English UI, setting persistence, close/restart, and real safe input/output.
- Installed-package Store screenshots.
- Windows App Certification Kit report.
- Live Partner Center identity re-copy and final listing review.
- Owner-approved logo, price, markets, IARC answers, privacy/support identity, EULA, and final third-party notices.

The first Scheduled API Runner install attempt failed with `0x800B0109` because the test certificate is not in `LocalMachine\\TrustedPeople`. No certificate-store change is authorized by this document. Never use `CurrentUser\\Root` or `LocalMachine\\Root`, and never weaken Windows security controls.

The unpacked MSIX includes Playwright browser payloads and browser ABOUT/license material. Installed-package Chromium launch and local-HTML workflows remain untested. Exact bundled-browser redistribution and customer-visible notices require owner/legal review.

Store submission, publication, main/release merge, external account access, and destructive customer-data operations are not authorized by this status note.
