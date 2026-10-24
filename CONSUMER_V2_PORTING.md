# Consumer -2 isolated sales-prep / migration handoff

Date: 2026-10-24 (Asia/Tokyo)
Source staging repository: shihuiarenjinba-png/browser-automation-runner
Source branch: codex/consumer-v2-store-prep-20261024
Target public EMPTY repository: shihuiarenjinba-png/Browser-Automation-Runner-2

## Status and work done
Guided setup, no-code step builder, preview and explicit live permission remain. User-facing final tab and instruction copy now favor ordinary users, while technical JSON is still available. This is not an AI recorder and should not be advertised as one.

## Sales and integrity HOLD
Real Windows GUI with headless/non-headless browser, site ToS controls, changed selectors, login timeout, error reporting and retry behavior. Customer-readable Playwright/Chromium/FFmpeg notices and SBOM/rights remain HOLD; do not mark third_party_rights_approved=true. New -2 product Store Identity is UNKNOWN.

The target repository has no initial commit. Never commit directly to main/release; code owner must bootstrap a nonmain branch in the target repository and then port the reviewed source. A staged branch on the old repo is not the -2 production repository. No Partner Center identity has been independently established for the -2 product. Do not build or upload a -2 MSIX with the old product's Identity / Store ID. No merge, signature, paid CI, submission or publication approval is given.

## Required release sequence
1. Create nonmain work branch on target -2 repository, port code and tests without replacing original.
2. Confirm the real user-visible features; do not advertise unimplemented integrations or AI.
3. Windows CI: Python tests, EXE self-test and unpacked runtime test at exact HEAD.
4. Independent Partner Center -2 product reservation, Identity/Publisher/PFN/version verification. Unknown => HOLD.
5. Build Store QA_UNSIGNED candidate only when Identity is documented; validate manifest, EXE and MSIX hashes and artifacts.
6. Windows installed application checks, screenshots at 1024x768 / 1280x720, privacy, error recovery, certification checks.
7. Only after explicit approval, submit to Partner Center and publish.

## Market evidence (not proof of sales)
- https://www.reddit.com/r/sideprojects/comments/1ww8let/i_built_an_opensource_tool_that_automatically/ (2026-10: file organization, avoid incomplete downloads, undo requests)
- https://www.reddit.com/r/software/comments/1tis5yj/mouzi_organize_downloads_folder_automatically/ (2026-05: local-first and manual mode requests)
- https://www.reddit.com/r/Playwright/comments/1tuyf33/for_people_using_browser_automation_in_real_work/ (2026-06: selector/session/hydration failures)
- https://www.reddit.com/r/automation/comments/1u1zu8f/those_of_you_who_recently_started_automating/ (2026-06: starting a workflow is the difficult step)
