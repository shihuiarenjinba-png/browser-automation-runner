# Browser Automation Runner — third-party notice status

Updated: 2026-11-16 JST

**ENGINEERING NOTICE BUNDLE IMPLEMENTED / HUMAN REDISTRIBUTION-RIGHTS REVIEW HOLD**

The Windows Store candidate bundles Playwright and the Playwright-provided Chromium
runtime next to the application executable.

## GitHub-side engineering controls

The Store build now:

1. reads the exact installed Playwright distribution;
2. copies its license/notice files into
   `THIRD_PARTY_NOTICES/playwright/`;
3. scans the exact `pw-browsers` payload for license/notice material and copies it
   into `THIRD_PARTY_NOTICES/runtime/` while preserving relative paths;
4. requires Chromium/Chrome notice evidence;
5. requires FFmpeg license evidence;
6. writes a customer-readable `THIRD_PARTY_NOTICES/README.md`;
7. generates `PACKAGE_INVENTORY.json` with SHA256 for every staged payload file;
8. packs the MSIX;
9. unpacks it again and verifies every inventory file/hash plus the notice bundle.

The CI Store artifact also exposes the generated notice directory and package
inventory outside the MSIX for operator review.

## Upstream license evidence

- Playwright for Python declares Apache-2.0:
  https://github.com/microsoft/playwright-python
- Playwright v1.62 uses Chromium 151.0.7922.34:
  https://github.com/microsoft/playwright-python/releases/tag/v1.62.0
- Chromium source/license materials are maintained upstream:
  https://chromium.googlesource.com/chromium/src/
- FFmpeg states that the project is LGPL 2.1+ by default, while optional GPL
  components can change the applicable license:
  https://ffmpeg.org/legal.html

## Remaining human gate

Presence and round-trip verification of notices does **not** automatically prove that
the exact Playwright-supplied browser/FFmpeg payload satisfies every commercial
redistribution obligation for this product.

Therefore `third_party_rights_approved` must remain false until the owner/legal
review inspects the exact generated notice bundle and final package inventory.

No code path may infer legal approval from successful CI.
