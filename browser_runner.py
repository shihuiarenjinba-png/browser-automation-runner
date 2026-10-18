from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
from pathlib import Path
from typing import Any

from playwright.sync_api import BrowserContext, Error as PlaywrightError, Page, Route, sync_playwright

from output_safety import OutputSafetyError, save_capture


class BrowserRunnerError(RuntimeError):
    pass


def resolve_env(value: Any) -> Any:
    if isinstance(value, str) and value.startswith("${ENV:") and value.endswith("}"):
        name = value[6:-1]
        result = os.getenv(name)
        if result is None:
            raise BrowserRunnerError(f"Missing environment variable: {name}")
        return result
    if isinstance(value, list):
        return [resolve_env(v) for v in value]
    if isinstance(value, dict):
        return {k: resolve_env(v) for k, v in value.items()}
    return value


class BrowserRunner:
    def __init__(self, config: dict[str, Any], dry_run: bool = False) -> None:
        self.config = resolve_env(config)
        self.dry_run = dry_run
        self.root = Path(self.config.get("root_dir", ".")).expanduser().resolve()
        self.allowed_hosts = {str(x).lower() for x in self.config.get("allow_hosts", [])}
        self.resource_hosts = {str(x).lower() for x in self.config.get("resource_hosts", [])}
        self.network_hosts = self.allowed_hosts | self.resource_hosts
        self.steps = self.config.get("steps", [])
        self.headless = bool(self.config.get("headless", True))
        self.timeout_ms = int(self.config.get("timeout_ms", 30_000))
        if not self.allowed_hosts:
            raise BrowserRunnerError("allow_hosts must not be empty")
        if not isinstance(self.steps, list) or not self.steps:
            raise BrowserRunnerError("steps must be a non-empty list")

    def _path(self, value: str) -> Path:
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = self.root / path
        path = path.resolve()
        try:
            path.relative_to(self.root)
        except ValueError as exc:
            raise BrowserRunnerError(f"Path is outside root_dir: {path}") from exc
        return path

    @staticmethod
    def _check_output(path: Path, overwrite: bool) -> None:
        if not path.exists():
            return
        if path.is_dir():
            raise BrowserRunnerError(f"Output path is a directory: {path}")
        if not overwrite:
            raise BrowserRunnerError(f"Output already exists and overwrite=false: {path}")

    def _assert_allowed_url(self, url: str) -> None:
        if url == "about:blank":
            return
        parsed = urllib.parse.urlparse(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https":
            raise BrowserRunnerError(f"Only HTTPS navigation is allowed: {url}")
        if host not in self.allowed_hosts:
            raise BrowserRunnerError(f"Top-level host is not allowed: {host}")

    def _route_guard(self, route: Route) -> None:
        parsed = urllib.parse.urlparse(route.request.url)
        if parsed.scheme in {"about", "data", "blob"}:
            route.continue_()
            return
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or host not in self.network_hosts:
            route.abort()
            return
        route.continue_()

    def _validate_step(self, step: dict[str, Any]) -> None:
        action = str(step.get("action", ""))
        allowed = {"goto", "fill", "click", "wait_for", "select_option", "check", "uncheck", "screenshot", "download"}
        if action not in allowed:
            raise BrowserRunnerError(f"Unsupported action: {action}")
        if action == "goto":
            self._assert_allowed_url(str(step["url"]))
        if action == "screenshot":
            self._path(str(step["path"]))
        if action == "download":
            self._path(str(step["save_as"]))

    def _run_step(self, page: Page, step: dict[str, Any]) -> None:
        action = str(step["action"])
        selector = str(step.get("selector", ""))

        if action == "goto":
            url = str(step["url"])
            self._assert_allowed_url(url)
            page.goto(url, wait_until=str(step.get("wait_until", "domcontentloaded")))
            self._assert_allowed_url(page.url)

        elif action == "fill":
            page.locator(selector).fill(str(step.get("value", "")))

        elif action == "click":
            page.locator(selector).click()
            page.wait_for_timeout(100)
            self._assert_allowed_url(page.url)

        elif action == "wait_for":
            page.locator(selector).wait_for(state=str(step.get("state", "visible")))

        elif action == "select_option":
            page.locator(selector).select_option(str(step["value"]))

        elif action == "check":
            page.locator(selector).check()

        elif action == "uncheck":
            page.locator(selector).uncheck()

        elif action == "screenshot":
            path = self._path(str(step["path"]))
            overwrite = bool(step.get("overwrite", False))
            self._check_output(path, overwrite)
            save_capture(path, lambda temporary: page.screenshot(path=str(temporary),
                         full_page=bool(step.get("full_page", False))), overwrite=overwrite)

        elif action == "download":
            path = self._path(str(step["save_as"]))
            overwrite = bool(step.get("overwrite", False))
            self._check_output(path, overwrite)
            def capture_download(temporary: Path) -> None:
                with page.expect_download() as download_info:
                    page.locator(selector).click()
                download_info.value.save_as(str(temporary))
                self._assert_allowed_url(page.url)
            save_capture(path, capture_download, overwrite=overwrite)

    def run(self) -> None:
        for step in self.steps:
            if not isinstance(step, dict):
                raise BrowserRunnerError("Each step must be an object")
            self._validate_step(step)

        if self.dry_run:
            print(json.dumps({
                "dry_run": True,
                "steps": len(self.steps),
                "allow_hosts": sorted(self.allowed_hosts),
                "resource_hosts": sorted(self.resource_hosts),
            }, ensure_ascii=False))
            return

        self.root.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context: BrowserContext = browser.new_context(accept_downloads=True)
            context.set_default_timeout(self.timeout_ms)
            context.route("**/*", self._route_guard)
            page = context.new_page()
            try:
                for index, step in enumerate(self.steps, start=1):
                    print(json.dumps({"step": index, "action": step.get("action")}, ensure_ascii=False))
                    self._run_step(page, step)
            finally:
                context.close()
                browser.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic Playwright browser runner")
    parser.add_argument("config", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        BrowserRunner(config, dry_run=args.dry_run).run()
        return 0
    except (OSError, json.JSONDecodeError, KeyError, ValueError, BrowserRunnerError, PlaywrightError, OutputSafetyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
