"""Read the launcher's shared mode/language preference.

Forecast (the toolkit launcher, ``paper-gui``) already keeps a working ``theme``/``language``
preference in ``%LOCALAPPDATA%\\Forecast\\settings.json``. Every program in the family is meant to
mirror that exactly -- same mode, same language -- and fall back to the system default only when
the file is not there at all (the launcher was never installed or run on this machine). This module
is the one shared implementation of that rule, so no consumer reimplements the fallback by hand.

Deliberately Qt-free and read-only: this package only ever reads the launcher's file, never writes
it -- Forecast itself owns writing it, from its own settings UI.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .palette import MODE_DARK, MODE_LIGHT

LANGUAGES = ("he", "en")


def shared_settings_path() -> Path:
    """Where Forecast keeps its settings -- ``%LOCALAPPDATA%\\Forecast\\settings.json``.

    Matches ``paper-gui/forecast/models.py``'s ``data_dir()``/``settings_path()`` exactly; this is
    a read-only mirror of that path, not a second definition of where the launcher's data lives.
    """
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~\\AppData\\Local")
    return Path(base) / "Forecast" / "settings.json"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def resolve_mode(*, prefers_light: bool | None) -> str:
    """"light" or "dark", mirroring the launcher's setting if it exists.

    Args:
        prefers_light: The OS appearance preference, used both when the launcher has no opinion
            and when the launcher itself is set to "system" -- so every program still ends up on
            the same resolved mode as the launcher, not just the same setting.
    """
    theme = _read_json(shared_settings_path()).get("theme")
    if theme in (MODE_LIGHT, MODE_DARK):
        return theme
    return MODE_LIGHT if prefers_light else MODE_DARK


def resolve_language(*, system_language: str) -> str:
    """"he" or "en", mirroring the launcher's setting if it exists, else the system default."""
    language = _read_json(shared_settings_path()).get("language")
    return language if language in LANGUAGES else system_language
