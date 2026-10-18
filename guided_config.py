"""Create a first-run navigation + screenshot example without browser side effects."""
from __future__ import annotations

import ipaddress
import json
import re
from pathlib import Path
from urllib.parse import urlsplit


class GuidedConfigError(ValueError):
    pass


def https_host(url: str) -> str:
    value = str(url).strip()
    if not value or any(c.isspace() for c in value):
        raise GuidedConfigError("Enter a full HTTPS URL / HTTPSのURLを入力してください")
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise GuidedConfigError("Invalid URL / URLの形式を確認してください") from exc
    if parsed.scheme != "https" or not host or parsed.username or parsed.password or parsed.fragment:
        raise GuidedConfigError("Only HTTPS without credentials or fragments is allowed")
    if parsed.query:
        raise GuidedConfigError("Remove URL query parameters; use advanced setup for query strings")
    if port is not None and port != 443:
        raise GuidedConfigError("Guided setup supports HTTPS port 443 only")
    if host == "localhost" or host.endswith(".local"):
        raise GuidedConfigError("Local hostnames are not supported by guided setup")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if not re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?", host) or "." not in host:
            raise GuidedConfigError("Enter a public DNS hostname / 公開ホスト名を入力してください")
        return host.lower()
    raise GuidedConfigError("IP literal addresses are not supported by guided setup")


def make_screenshot_workflow(*, root_dir: str, url: str, filename: str) -> dict:
    root_value = str(root_dir).strip()
    if not root_value:
        raise GuidedConfigError("Select a data folder first / 最初に保存先フォルダーを選択してください")
    root = Path(root_value).expanduser()
    if not root.is_dir():
        raise GuidedConfigError("Choose an existing folder for outputs / 保存先フォルダーを指定してください")
    host = https_host(url)
    filename = str(filename).strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,90}\.png", filename, re.IGNORECASE):
        raise GuidedConfigError("Use a safe .png file name, e.g. capture.png")
    if filename.startswith(".") or filename.lower() in {"con.png", "prn.png", "aux.png", "nul.png"}:
        raise GuidedConfigError("This output file name is reserved")
    return {
        "root_dir": str(root.resolve()),
        "headless": True,
        "timeout_ms": 30000,
        "allow_hosts": [host],
        "resource_hosts": [],
        "steps": [
            {"action": "goto", "url": str(url).strip()},
            {"action": "screenshot", "path": "screenshots/" + filename,
             "full_page": True, "overwrite": False},
        ],
    }


def save_new_config(path: str | Path, config: dict) -> Path:
    destination = Path(path)
    with destination.open("x", encoding="utf-8") as handle:
        json.dump(config, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return destination
