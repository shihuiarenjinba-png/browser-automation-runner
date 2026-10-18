"""Strict configuration builder shared by the desktop editor and unit tests."""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit


class EditorError(ValueError):
    pass


ACTIONS = ("goto", "fill", "click", "wait_for", "select_option",
           "check", "uncheck", "screenshot", "download")


def hosts_from_text(value: str) -> list[str]:
    hosts = [v.strip().lower() for v in value.replace("\n", ",").split(",")]
    hosts = [v for v in hosts if v]
    if not hosts or len(hosts) != len(set(hosts)):
        raise EditorError("Specify unique allowed HTTPS hostnames")
    for host in hosts:
        if not re.fullmatch(r"[a-z0-9-]+(?:\.[a-z0-9-]+)*", host):
            raise EditorError("Hostname must not contain schemes, ports or wildcards")
    return hosts


def make_step(action: str, target: str, value: str = "") -> dict:
    if action not in ACTIONS:
        raise EditorError("Unsupported browser action")
    target, value = target.strip(), value.strip()
    if not target:
        raise EditorError("The URL, CSS selector or output path is required")
    if action == "goto":
        parsed = urlsplit(target)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
            raise EditorError("Navigation requires a HTTPS URL without credentials")
        return {"action": action, "url": target}
    if action in ("fill", "select_option"):
        if not value:
            raise EditorError("This action requires a value")
        return {"action": action, "selector": target, "value": value}
    if action == "download":
        if not value:
            raise EditorError("Download requires a destination path")
        return {"action": action, "selector": target, "save_as": value}
    if action == "screenshot":
        return {"action": action, "path": target, "full_page": True}
    if action == "wait_for":
        return {"action": action, "selector": target, "state": "visible"}
    return {"action": action, "selector": target}


def make_config(root: str, host_text: str, steps: list[dict],
                resource_text: str = "") -> dict:
    if not root.strip():
        raise EditorError("Select a working folder")
    if not steps:
        raise EditorError("Add at least one action")
    hosts = hosts_from_text(host_text)
    resource_hosts = hosts_from_text(resource_text) if resource_text.strip() else []
    config = {
        "root_dir": str(Path(root).expanduser().resolve()),
        "headless": True,
        "timeout_ms": 30000,
        "allow_hosts": hosts,
        "resource_hosts": resource_hosts,
        "steps": steps,
    }
    for step in steps:
        if not isinstance(step, dict):
            raise EditorError("Invalid step")
        action = step.get("action")
        if action not in ACTIONS:
            raise EditorError("Unsupported step in workflow")
        if action == "goto" and urlsplit(str(step.get("url", ""))).hostname not in hosts:
            raise EditorError("Navigation target must be an allowed host")
    return config
