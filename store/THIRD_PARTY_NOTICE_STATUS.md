# Browser Automation Runner — third-party notice status

Status: RELEASE HOLD until the exact final package is reviewed.

The current Windows validation build bundles Playwright and its Chromium runtime next to the application executable. The Store build verifies that a Chromium executable remains present after the MSIX pack/unpack round trip.

Before commercial release, preserve customer-readable license/notice material for the exact bundled Playwright/Chromium/FFmpeg payload and record a final package SBOM. This file does not declare third-party rights approved; `third_party_rights_approved` remains false in the MSIX validation report.
