# Bundled browser provenance audit — 2026-11-16

**ENGINEERING PROVENANCE PASS / HUMAN REDISTRIBUTION-RIGHTS REVIEW HOLD**

## Exact runtime contract

The product pins Playwright Python `>=1.62,<1.63`; current CI resolves the 1.62
line. Playwright 1.62's published browser version is Chromium 151.0.7922.34.

The build:

- freezes Browser Automation Runner;
- sets a private `PLAYWRIGHT_BROWSERS_PATH`;
- installs Playwright Chromium into the candidate payload;
- runs the packaged no-network self-test;
- runs the packaged bundled-Chromium offline smoke;
- copies the whole payload into the MSIX stage;
- validates that Chromium remains present after MakeAppx pack/unpack.

## Notice/provenance bundle

`store/collect_browser_notices.py` collects evidence from the exact build:

- Playwright distribution license/notice files;
- browser-runtime LICENSE / COPYING / NOTICE / ABOUT style files;
- FFmpeg license material;
- customer-readable notice index;
- SHA256 package inventory.

`store/build_msix_draft.ps1` then checks after MSIX unpack that:

- the notice bundle is still present;
- the package inventory itself is unchanged;
- every inventoried staged file exists;
- every inventoried staged file has the same SHA256;
- BrowserAutomationRunner.exe has the same SHA before/after packaging;
- at least one bundled Chromium executable remains present.

The validation report records:

- `third_party_notice_bundle_verified=true`;
- `package_inventory_verified=true`;
- inventory count;
- `third_party_rights_approved=false`.

## Human rights decision

GitHub engineering can prove what bytes and notices are bundled. It cannot make the
owner/legal decision that those terms are acceptable for the intended distribution.

Keep release HOLD until the exact final artifact's notices/inventory are reviewed.
Do not flip `third_party_rights_approved` merely because CI passes.

Upstream references:

- https://github.com/microsoft/playwright-python
- https://github.com/microsoft/playwright
- https://chromium.googlesource.com/chromium/src/
- https://ffmpeg.org/legal.html
