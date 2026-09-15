# Roadmap

## Phase 1 — Deterministic Browser Core（現在）

- Playwright / Chromium
- explicit action list
- HTTPS-only top-level navigation
- top-level host allowlist
- network/resource host allowlist
- local output path boundary
- Dry Run
- default no-overwrite for screenshots/downloads
- `${ENV:NAME}` secret references

## Phase 2 — Reliability

- selector diagnostics
- explicit navigation waits
- download verification
- session profile handling without committing cookies/tokens
- per-step retry where safe
- structured execution log

## Phase 3 — Usability

- selector recorder/helper
- GUI workflow editor
- reusable site profiles
- Windows packaging

## Policy

Official API > local processing > browser automation. Browser automation remains the last-resort adapter and will not include LLM/AI autonomous browsing in the default product.

## Release Gate

Allowed-host escape tests, redirect tests, download-path tests, credential-leak review, representative-site regression tests, browser-version compatibility tests, Windows 10/11 smoke tests.
