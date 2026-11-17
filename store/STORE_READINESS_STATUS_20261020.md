# Browser Automation Runner — Store readiness status

Updated: 2026-11-16 JST

**GITHUB ENGINEERING COMPLETE PENDING FINAL EXACT-HEAD CI / LOCAL BROWSER QA + HUMAN RIGHTS REVIEW HOLD / STORE WRITE HOLD**

Repository branch: `codex/browser-standard-consumer-ui-20261113`  
Draft PR: #8

## GitHub-side implemented

- bilingual guided browser workflow;
- Dry Run / explicit live-execution guard;
- navigation and output-collision safety tests;
- bundled Playwright Chromium runtime;
- packaged no-network self-test and Chromium offline smoke;
- unsigned MSIX build;
- Store Identity / Publisher / Version validation;
- MakeAppx pack/unpack and EXE/browser roundtrip checks;
- exact-package `store-product-handoff/2` generation;
- customer-readable Playwright/Chromium/FFmpeg notice collection;
- SHA256 `PACKAGE_INVENTORY.json`;
- post-unpack verification of every inventoried staged file;
- local final-QA runbook and Store/compliance evidence bundled with the Store artifact.

The latest exact-head Windows build and reliability workflows must both be SUCCESS
before downloading the candidate.

## Canonical Store identity

- Store ID: `9NQHC8VW729G`
- Identity: `OkinawaDesktopTools.BrowserAutomationRunner`
- Publisher: `CN=46263F21-A700-41DB-8C9B-114C22FB82FC`
- PFN: `OkinawaDesktopTools.BrowserAutomationRunner_j8yefg9jgfh58`
- technical MSIX version: `1.0.0.0`

Live Partner Center reverification remains mandatory.

## Third-party boundary

GitHub engineering now proves what notice/inventory bytes are shipped and that they
survive MSIX packaging. It deliberately does **not** set
`third_party_rights_approved=true`.

Human owner/legal review of the exact final Playwright/Chromium/FFmpeg payload remains
a release gate.

## Commercial position

Launch model: FREE candidate.

## Local-only remaining gates

- exact artifact SHA verification;
- physical JP/EN + 100/125/150% DPI;
- bundled Chromium launch;
- harmless test-site navigation/screenshot;
- click/input/wait/select/download;
- unsafe/local/private navigation rejection;
- no-overwrite/output-collision behavior;
- error/re-run UX;
- human third-party-rights review of exact notice/inventory;
- live Partner Center reverify;
- owner assets/security/audience review.

Return PASS through an exact-package `local-final-qa-receipt/1`, then proceed through
VALIDATE_ONLY -> DRY_RUN -> separately approved package upload. Certification and
Publish remain separate gates.
