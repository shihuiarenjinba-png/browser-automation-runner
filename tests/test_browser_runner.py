from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from browser_runner import BrowserRunner, BrowserRunnerError


class FakeRequest:
    def __init__(self, url: str, navigation: bool) -> None:
        self.url = url
        self._navigation = navigation

    def is_navigation_request(self) -> bool:
        return self._navigation


class FakeRoute:
    def __init__(self, url: str, navigation: bool) -> None:
        self.request = FakeRequest(url, navigation)
        self.action: str | None = None
        self.error_code: str | None = None

    def continue_(self) -> None:
        self.action = "continue"

    def abort(self, error_code: str | None = None) -> None:
        self.action = "abort"
        self.error_code = error_code


def runner(root: Path) -> BrowserRunner:
    return BrowserRunner({
        "root_dir": str(root),
        "allow_hosts": ["app.example"],
        "resource_hosts": ["cdn.example"],
        "steps": [{"action": "goto", "url": "https://app.example/"}],
    }, dry_run=True)


class BrowserRunnerTests(unittest.TestCase):
    def test_allowed_top_level_navigation_continues(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            r = runner(Path(tmp))
            route = FakeRoute("https://app.example/page", True)
            r._route_guard(route)  # type: ignore[arg-type]
            self.assertEqual(route.action, "continue")

    def test_resource_host_cannot_be_used_for_navigation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            r = runner(Path(tmp))
            route = FakeRoute("https://cdn.example/popup", True)
            r._route_guard(route)  # type: ignore[arg-type]
            self.assertEqual(route.action, "abort")

    def test_resource_host_is_allowed_for_subresources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            r = runner(Path(tmp))
            route = FakeRoute("https://cdn.example/app.js", False)
            r._route_guard(route)  # type: ignore[arg-type]
            self.assertEqual(route.action, "continue")

    def test_data_url_cannot_be_top_level_navigation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            r = runner(Path(tmp))
            route = FakeRoute("data:text/html,hello", True)
            r._route_guard(route)  # type: ignore[arg-type]
            self.assertEqual(route.action, "abort")

    def test_data_url_may_be_subresource(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            r = runner(Path(tmp))
            route = FakeRoute("data:image/png;base64,AA==", False)
            r._route_guard(route)  # type: ignore[arg-type]
            self.assertEqual(route.action, "continue")

    def test_empty_selector_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            r = runner(Path(tmp))
            with self.assertRaisesRegex(BrowserRunnerError, "non-empty selector"):
                r._validate_step({"action": "click", "selector": ""})

    def test_out_of_range_timeout_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(BrowserRunnerError, "timeout_ms"):
                BrowserRunner({
                    "root_dir": tmp,
                    "allow_hosts": ["app.example"],
                    "steps": [{"action": "goto", "url": "https://app.example/"}],
                    "timeout_ms": 0,
                }, dry_run=True)


if __name__ == "__main__":
    unittest.main()
