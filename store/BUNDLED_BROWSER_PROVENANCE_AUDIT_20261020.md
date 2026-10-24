# Bundled browser provenance audit — 2026-10-20

**DRAFT / LEGAL REVIEW REQUIRED**

Store-candidate MSIX SHA256: `7f4b07befa776b9daafbbd42a5db56981da307b740b8afe5e4a6e4dc91e43419`.

## Exact runtime

- Playwright Python: 1.62.0; wheel metadata declares Apache-2.0.
- `browsers.json`: Chrome for Testing 151.0.7922.34 revision 1234; Chrome Headless Shell 151.0.7922.34 revision 1234; FFmpeg revision 1011; winldd revision 1007.
- Build path: `build_windows.ps1` sets `PLAYWRIGHT_BROWSERS_PATH`, runs `python -m playwright install chromium`, then the MSIX builder recursively copies the payload. No source patch or binary rewrite step was found.
- `chrome.exe` source payload and unpacked MSIX: 4,024,832 bytes, SHA256 `409805a16d6416087e6b2f778df1cf8f7bbb267d6b99f6b5bb0a618eace234f2`. This proves this packaging round trip did not modify the executable; it does not independently authenticate the upstream archive.
- The Chrome/Headless Shell, FFmpeg, and winldd executables checked here are not Authenticode-signed.

## Notices

The unpacked MSIX preserves Chrome/Chromium `ABOUT`, `LICENSE.headless_shell`, and FFmpeg `COPYING.LGPLv2.1`. Playwright's `LICENSE`, `NOTICE`, and `ThirdPartyNotices.txt` exist in the build environment but are not exposed as plainly named top-level customer notice files in the unpacked MSIX.

Before sale: add a customer-readable notices location, generate/scan the final unpacked-package SBOM, preserve all browser notices, repeat hash comparison, and obtain owner/legal approval for paid redistribution of the exact Chrome for Testing payload.

References:

- https://github.com/microsoft/playwright-python/blob/main/pyproject.toml
- https://github.com/microsoft/playwright/blob/main/NOTICE
- https://chromium.googlesource.com/chromium/src/+/HEAD/docs/adding_to_third_party.md
