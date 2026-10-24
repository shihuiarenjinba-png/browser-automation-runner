# Sales release checklist / 販売直前チェック

## Automated / code gates

- [x] Navigation limited to `allow_hosts`
- [x] `resource_hosts` cannot be used for top-level/popup navigation
- [x] Service Workers blocked; context routing covers popup pages
- [x] URL userinfo/top-level data/blob restrictions
- [x] Secret/query/fragment-minimized UI preview
- [x] Explicit **`言語 / Language`** selector with persisted `日本語` / `English`
- [x] Language and advanced-warning regression tests
- [x] Japanese and English user guides

## Real Windows/browser gates

- [ ] Windows 10 smoke test
- [ ] Windows 11 smoke test
- [ ] Switch 日本語 → English → 日本語; restart and confirm persistence
- [ ] Check 100%, 125%, 150% display scaling
- [ ] Validate a controlled config without launching live browser actions
- [ ] Confirm Dry Run performs no click/type/download/navigation actions
- [ ] Confirm an unapproved navigation host is blocked in main page, popup, and iframe cases
- [ ] Confirm `resource_hosts` resources load while navigation to those hosts remains blocked
- [ ] Confirm Service Worker registration/network bypass is blocked
- [ ] Test one controlled click/form flow on a dedicated non-production account
- [ ] Test controlled download and screenshot paths inside the allowed root
- [ ] Verify URL query/fragment/credentials and fill secrets are not shown in UI/log screenshots
- [ ] Verify website-side failures stop visibly rather than silently continuing
- [ ] Reconfirm that every shipped browser workflow lacks a safer official API/local alternative
- [ ] Review the target site's current Terms/automation restrictions before sale
- [ ] Build packaged Windows distribution including the validated Playwright/Chromium version
- [ ] Run Windows Defender/AV scan and record release SHA-256
- [ ] Prepare LICENSE/NOTICE/SBOM and lock Playwright/browser dependencies
- [ ] Sign the final installer/executable if distributed commercially

Do not market or release this as a general “works on any website” automation tool. Every shipped workflow must be explicitly supported and revalidated.

未チェック項目が残っている間は販売完成扱いにしません。
