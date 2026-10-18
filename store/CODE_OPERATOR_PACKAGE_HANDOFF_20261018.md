# Code operator → Microsoft Store packaging handoff (2026-10-18)

## Decision and role boundary

The owner requests **UI/feature/integration-first source development**, then
delegates Windows launch tests, build/package creation and technical validation
to the separate code operator. A Draft PR is the handoff source, not a
certified binary. Do not claim a PASS without a log from the exact commit.

Use **the indicated existing GitHub branch only** in an isolated new Windows
working directory. Do not edit `main`, overwrite any published EXE/MSIX,
delete source branches, alter customer files, reuse another SKU's Store
identity, or merge a layered PR out of order. Preserve logs and test fixtures
without secrets. All source fixes must be committed to a dedicated branch
and linked to a reviewable PR; do not quietly patch a packaged artifact.

## Standard Windows acceptance gate

1. Capture the current branch's **exact full Git SHA**. Run:
   `python -m compileall -q .`
   and `python -m unittest discover -s tests -v`.
   Do not ship if even one test fails, skips a required Windows feature or
   if expected GUI actions do not execute. Keep the complete redacted logs.
2. Open the real GUI at 100%, 125%, 150% DPI in Japanese and English. Verify
   no clipping, unusable hidden actions, labels inconsistent with features,
   keyboard-only tab navigation, and that user data persists as described.
3. Exercise the exact UI → configuration → offline preview → explicit
   live confirmation → safe output → restart flow on authorized synthetic
   fixtures. Repeat, fail mid-operation, change settings after preview, and
   test existing-file collisions. Never use real customers' data.
4. Build fresh EXE in a unique new output path; test both source and packaged
   `--self-test` modes and any product-specific runtime smoke.
5. Build a **Store-appropriate MSIX / MSIXBundle** with the exact reserved
   Name and Publisher copied from Partner Center. Validate signing requirements,
   required assets/rights, dependencies, icons, package architecture,
   install, launch, update, uninstall and Windows App Certification Kit/Store
   validations. Store upload requires the MSIX file, **not** merely an EXE ZIP.
6. Validate file/secret protection, logs, startup registrations and persistence
   across the install/update/uninstall lifecycle, including different users.
7. Prepare actual JP/EN Store screenshots from the built UI, final listing,
   support/privacy URL, license/third-party notice evidence and pricing
   review. Use the owner's existing product slot only.
8. Report in one evidence table: SHA; Python tests; GUI JP/EN 100/125/150%;
   live synthetic workflow; frozen EXE; MSIX manifest; Windows install/update;
   WACK/Store certification; security and data; license and screenshots;
   all PASS/FAIL/BLOCKED with log/artifact paths. If a gate fails, send the
   exact failure back for repair without claiming sales readiness.

**GitHub Actions caveat:** private sibling repositories' hosted CI jobs have
failed before allocating any runner steps (and the job logs could not be
downloaded); this is not proof that test code failed. Investigate Actions
billing/permissions/runner allocation without buying more allowance without
the owner's approval. Use local Windows operator verification meanwhile.

Do not submit to Partner Center automatically; owner reviews the completed
package and explicitly authorizes the actual submission.

## This product

- Product: **Browser Automation Runner**
- Reserved Microsoft Store ID: `9NQHC8VW729G`
- Package Identity Name: `OkinawaDesktopTools.BrowserAutomationRunner`
- Package Publisher: `CN=46263F21-A700-41DB-8C9B-114C22FB82FC`
- Publisher display name: `Okinawa Desktop Tools`
- Source: `shihuiarenjinba-png/browser-automation-runner` / Draft PR #3: https://github.com/shihuiarenjinba-png/browser-automation-runner/pull/3
- Full source branch (do not use only PR base): `feat/browser-no-code-steps-20261018`
- Actual desktop GUI entrypoint: `desktop_app.py`
- Initial non-sales validation command: `powershell -ExecutionPolicy Bypass -File .\build_windows.ps1`
- This source can be handed over for operator verification, but do not mark binary PASS until logs exist.

## Product-specific end-to-end scenario

Enter owned HTTPS page and screenshot destination in Start Here; open Build
Steps, choose human-language Click, Fill, Wait, Select, Check or Download
operations. Confirm ordered append, double-click load, Replace selected step,
remove and reorder. Save new workflow JSON (never overwrite old), check offline
Dry Run, then explicitly approve real browser execution. Validate clicks/forms
only on authorized synthetic HTTPS test pages; verify screenshot and download
output collisions, credentials via ENV references, blocked cross-host redirects,
timeouts and failures. CSS selectors can fail when the site changes and this
is not AI browsing; test understandable feedback.

Build recipe `build_windows.ps1` must stage Playwright Chromium under adjacent
`pw-browsers` next to the EXE. A frozen app must refuse to fall back to a
browser in the operator's personal cache. Run `desktop_app.py --self-test`
and packaged `--browser-smoke` against about:blank, then execute a synthetic
real HTTPS workflow with the full packaged directory. **The MSIX must contain
the Chromium runtime folder, not just BrowserAutomationRunner.exe**.
Validate third-party Chromium/Playwright license notices and Store size
constraints. Tests: `tests/test_no_code_steps.py`,
`tests/test_guided_config.py`, `tests/test_output_collision.py`.

## Where to send evidence

Record build report, SHA256 of tested binaries, new MSIX name/version,
real JP/EN GUI screenshots, redacted test results and final QA decision in
an additional dated file under `store/` on the same product branch. Surface
every discovered source defect in a follow-up PR. Keep `main` and any
previous release unchanged until separately authorized.
