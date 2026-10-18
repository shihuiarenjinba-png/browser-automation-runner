"""Constrained no-code browser workflow assembler: offline configuration only."""
from __future__ import annotations

from pathlib import Path
import re
from guided_config import GuidedConfigError, make_screenshot_workflow

_CHOICES = {"click", "fill", "wait_for", "select_option", "check", "uncheck", "download"}
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,90}$")
_ENV = re.compile(r"^\$\{ENV:[A-Za-z_][A-Za-z0-9_]*\}$")


def build_extra_step(*, action: str, selector: str, value: str = "", filename: str = "") -> dict:
    action = str(action).strip()
    selector = str(selector).strip()
    if action not in _CHOICES:
        raise GuidedConfigError("Only predefined browser actions are supported")
    if not selector or len(selector) > 250 or any(ord(c) < 32 for c in selector):
        raise GuidedConfigError("Enter a CSS selector up to 250 characters")
    step = {"action": action, "selector": selector}
    if action in {"fill", "select_option"}:
        if len(str(value)) > 400 or any(ch in str(value) for ch in "\r\n"):
            raise GuidedConfigError("Input must be one line, at most 400 characters")
        sensitive = any(x in selector.lower() for x in ("password", "token", "secret", "api-key"))
        if sensitive and not _ENV.fullmatch(str(value)):
            raise GuidedConfigError("Sensitive inputs must refer to an environment variable")
        if not str(value):
            raise GuidedConfigError("Fill/select requires a non-empty value")
        step["value"] = str(value)
    if action == "download":
        filename = str(filename).strip()
        if not _NAME.fullmatch(filename) or filename.endswith(".") or ".." in filename:
            raise GuidedConfigError("Choose a simple new filename without path separators")
        stem = filename.lower().split(".")[0]
        if stem in {"con", "prn", "aux", "nul"} or re.fullmatch(r"(com|lpt)[1-9]", stem):
            raise GuidedConfigError("Reserved Windows output name")
        step.update({"save_as": "downloads/" + filename, "overwrite": False})
    return step


def build_nocode_workflow(*, root_dir: str, url: str, screenshot: str,
                          additional_steps: list[dict]) -> dict:
    """Construct approved page -> user steps -> safe screenshot; no browser launch."""
    if not isinstance(additional_steps, list) or len(additional_steps) > 20:
        raise GuidedConfigError("Choose at most 20 steps per workflow")
    base = make_screenshot_workflow(root_dir=root_dir, url=url, filename=screenshot)
    validated = []
    for step in additional_steps:
        if not isinstance(step, dict):
            raise GuidedConfigError("Each step must be an object")
        if step.get("action") == "download":
            relative = str(step.get("save_as", ""))
            if not relative.startswith("downloads/") or "/" in relative[len("downloads/"):] or "\\" in relative:
                raise GuidedConfigError("Downloads must use a simple path under downloads/")
        validated.append(build_extra_step(
            action=step.get("action", ""), selector=step.get("selector", ""),
            value=step.get("value", ""),
            filename=Path(str(step.get("save_as", ""))).name
            if step.get("action") == "download" else "",
        ))
    base["steps"] = [base["steps"][0], *validated, base["steps"][-1]]
    return base
