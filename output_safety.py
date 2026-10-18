"""Atomic browser capture/download output that never deletes a user file first."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Callable


class OutputSafetyError(ValueError):
    pass


def save_capture(destination: Path, produce: Callable[[Path], None], overwrite: bool = False) -> None:
    """Produce to an adjacent temporary file and commit only after success.

    A no-overwrite output uses atomic hardlink creation and fails if a collision
    appears during capture. Filesystems without hardlink support fail closed.
    """
    path = Path(destination)
    if path.exists() and path.is_dir():
        raise OutputSafetyError('Destination is a directory')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw = tempfile.mkstemp(prefix='.' + path.stem + '-capture-', suffix=path.suffix or '.bin', dir=path.parent)
    os.close(fd)
    temporary = Path(raw)
    try:
        produce(temporary)
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise OutputSafetyError('Capture produced an empty output')
        if overwrite:
            os.replace(temporary, path)
        else:
            try:
                os.link(temporary, path)
            except FileExistsError as exc:
                raise OutputSafetyError('Output already exists; no overwrite performed') from exc
    finally:
        temporary.unlink(missing_ok=True)
