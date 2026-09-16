# Browser Automation Runner — User Guide

## Positioning

This is an **advanced fallback**. Prefer an API or local deterministic implementation whenever one is available. Browser automation can break when the website UI changes.

Use **`言語 / Language`** in the upper-right corner to choose `日本語` or `English`. The selection is retained on the next launch.

## Normal workflow

1. Choose the Browser Automation JSON.
2. Use `Validate` to inspect allowed hosts, resource-only hosts, and steps.
3. Run `Dry Run / Validate`. Dry Run does not execute browser actions.
4. Use `Run Browser` only after confirming there is no appropriate API/local alternative, the target account is correct, and the steps are expected.

## Safety behavior

- Navigation is limited to `allow_hosts`.
- `resource_hosts` is only for subresources such as JS/CSS/images, not navigation.
- Service Workers are blocked.
- Query strings, fragments, and URL credentials are not intentionally shown in the normal UI.
- A side-effect warning is shown before live browser execution.

Complete all applicable items in `SALES_RELEASE_CHECKLIST.md` before commercial distribution.
