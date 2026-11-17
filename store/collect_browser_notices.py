#!/usr/bin/env python3
"""Collect customer-readable Playwright/Chromium/FFmpeg notices into the MSIX stage.

This is an engineering compliance aid, not legal approval. It copies notice/license
material from the exact installed Playwright distribution and exact bundled browser
payload, then writes a SHA-256 package inventory.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import shutil
from pathlib import Path

NOTICE_NAMES = {
    "about",
    "notice",
    "notice.txt",
    "thirdpartynotices.txt",
    "third_party_notices.txt",
}
NOTICE_PREFIXES = ("license", "copying")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_notice(path: Path) -> bool:
    name = path.name.lower()
    return name in NOTICE_NAMES or name.startswith(NOTICE_PREFIXES)


def copy_playwright_notices(destination: Path) -> list[Path]:
    dist = importlib.metadata.distribution("playwright")
    copied: list[Path] = []
    for entry in dist.files or []:
        source = Path(dist.locate_file(entry))
        if not source.is_file() or not is_notice(source):
            continue
        target = destination / "playwright" / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(source, target)
            copied.append(target)
    if not copied:
        raise RuntimeError("Playwright license/notice files were not found in the installed distribution")
    return copied


def copy_runtime_notices(payload: Path, destination: Path) -> list[Path]:
    browser_root = payload / "pw-browsers"
    if not browser_root.is_dir():
        raise RuntimeError("pw-browsers payload is missing")
    copied: list[Path] = []
    for source in sorted(p for p in browser_root.rglob("*") if p.is_file() and is_notice(p)):
        relative = source.relative_to(browser_root)
        target = destination / "runtime" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(target)
    if not copied:
        raise RuntimeError("No bundled-browser notice files were found")
    names = [str(p).lower() for p in copied]
    if not any("chromium" in n or "chrome" in n or n.endswith("/about") or n.endswith("\\about") for n in names):
        raise RuntimeError("Chromium/Chrome notice evidence was not found")
    if not any("ffmpeg" in n and ("copying" in n or "license" in n) for n in names):
        raise RuntimeError("FFmpeg license evidence was not found")
    return copied


def write_readme(destination: Path, playwright_files: list[Path], runtime_files: list[Path]) -> None:
    text = """# Third-party notices bundled with Browser Automation Runner

This directory is generated from the exact build environment and bundled browser
runtime. The copied license/notice files remain authoritative for their respective
components.

Components include Playwright for Python, the Playwright-provided Chromium runtime,
and the FFmpeg payload shipped with that runtime. This application does not claim
ownership of those third-party components.

Engineering references:
- Playwright Python: https://github.com/microsoft/playwright-python
- Playwright: https://github.com/microsoft/playwright
- Chromium: https://chromium.googlesource.com/chromium/src/
- FFmpeg legal information: https://ffmpeg.org/legal.html

Presence of these files does not itself constitute owner/legal approval for
redistribution. The exact final package must still pass the repository's human
third-party-rights release gate.
"""
    (destination / "README.md").write_text(text, encoding="utf-8")


def write_inventory(stage: Path) -> dict:
    inventory_path = stage / "PACKAGE_INVENTORY.json"
    files = []
    for path in sorted(p for p in stage.rglob("*") if p.is_file() and p != inventory_path):
        files.append({
            "path": path.relative_to(stage).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    payload = {
        "schema_version": "browser-msix-package-inventory/1",
        "file_count": len(files),
        "files": files,
    }
    inventory_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload-dir", required=True)
    parser.add_argument("--stage-dir", required=True)
    args = parser.parse_args()

    payload = Path(args.payload_dir).resolve()
    stage = Path(args.stage_dir).resolve()
    if not payload.is_dir() or not stage.is_dir():
        raise SystemExit("payload/stage directory missing")

    destination = stage / "THIRD_PARTY_NOTICES"
    if destination.exists():
        raise SystemExit("THIRD_PARTY_NOTICES already exists; refusing to overwrite evidence")
    destination.mkdir(parents=True)

    playwright_files = copy_playwright_notices(destination)
    runtime_files = copy_runtime_notices(payload, destination)
    write_readme(destination, playwright_files, runtime_files)
    inventory = write_inventory(stage)

    report = {
        "status": "PASS",
        "playwright_notice_count": len(playwright_files),
        "runtime_notice_count": len(runtime_files),
        "package_inventory_count": inventory["file_count"],
    }
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
