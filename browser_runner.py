from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
from pathlib import Path
from typing import Any

from playwright.sync_api import BrowserContext, Error as PlaywrightError, Page, Route, sync_playwright


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
        self.allowed_hosts = {str(x).strip().lower() for x in self.config.get("allow_hosts", []) if str(x).strip()}
        self.resource_hosts = {str(x).strip().lower() for x in self.config.get("resource_hosts", []) if str(x).strip()}
        self.network_hosts = self.allowed_hosts | self.resource_hosts
        self.steps = self.config.get("steps", [])
        self.headless = bool(self.config.get("headless", True))
        self.timeout_ms = int(self.config.get("timeout_ms", 30_000))
        if not 1_000 <= self.timeout_ms <= 120_000:
            raise BrowserRunnerError("timeout_ms must be between 1000 and 120000")
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
        if parsed.username or parsed.password:
            raise BrowserRunnerError("Credentials in navigation URL are not allowed")
        if parsed.scheme != "https":
            raise BrowserRunnerError(f"Only HTTPS navigation is allowed: {url}")
        if host not in self.allowed_hosts:
            raise BrowserRunnerError(f"Top-level host is not allowed: {host}")

    def _route_guard(self, route: Route) -> None:
        request = route.request
        url = request.url
        parsed = urllib.parse.urlparse(url)

        # Every navigation request, including popup and iframe navigations, is
        # restricted to allow_hosts. resource_hosts are subresources only.
        if request.is_navigation_request():
            if url == "about:blank":
                route.continue_()
                return
            host = (parsed.hostname or "").lower()
            if parsed.username or parsed.password or parsed.scheme != "https" or host not in self.allowed_hosts:
                route.abort(error_code="blockedbyclient")
                return
            route.continue_()
            return

        # Non-navigation resources may additionally use explicitly-approved
        # resource hosts. data/blob/about are allowed only as subresources.
        if parsed.scheme in {"about", "data", "blob"}:
            route.continue_()
            return
        host = (parsed.hostname or "").lower()
        if parsed.username or parsed.password or parsed.scheme != "https" or host not in self.network_hosts:
            route.abort(error_code="blockedbyclient")
            return
        route.continue_()

    def _validate_step(self, step: dict[str, Any]) -> None:
        action = str(step.get("action", ""))
        allowed = {"goto", "fill", "click", "wait_for", "select_option", "check", "uncheck", "screenshot", "download"}
        if action not in allowed:
            raise BrowserRunnerError(f"Unsupported action: {action}")
        if action == "goto":
            self._assert_allowed_url(str(step["url"]))
        if action in {"fill", "click", "wait_for", "select_option", "check", "uncheck", "download"}:
            selector = step.get("selector")
            if not isinstance(selector, str) or not selector.strip():
                raise BrowserRunnerError(f"{action} requires a non-empty selector")
        if action == "select_option" and "value" not in step:
            raise BrowserRunnerError("select_option requires value")
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
            path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(path), full_page=bool(step.get("full_page", False)))

        elif action == "download":
            path = self._path(str(step["save_as"]))
            overwrite = bool(step.get("overwrite", False))
            self._check_output(path, overwrite)
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_name(path.name + ".download.tmp")
            temp.unlink(missing_ok=True)
            try:
                with page.expect_download() as download_info:
                    page.locator(selector).click()
                download = download_info.value
                failure = download.failure()
                if failure:
                    raise BrowserRunnerError(f"Download failed: {failure}")
                download.save_as(str(temp))
                if not temp.is_file():
                    raise BrowserRunnerError("Download did not produce a file")
                if path.exists() and overwrite:
                    path.unlink()
                os.replace(temp, path)
            finally:
                temp.unlink(missing_ok=True)
            self._assert_allowed_url(page.url)

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
            # Blocking service workers ensures context.route sees outbound HTTP(S)
            # traffic rather than allowing a service worker to bypass the guard.
            context: BrowserContext = browser.new_context(accept_downloads=True, service_workers="block")
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
    except (OSError, json.JSONDecodeError, KeyError, ValueError, BrowserRunnerError, PlaywrightError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
