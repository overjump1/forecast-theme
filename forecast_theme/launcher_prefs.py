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


def _data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~\\AppData\\Local")
    return Path(base) / "Forecast"


def shared_settings_path() -> Path:
    """Where Forecast keeps its settings -- ``%LOCALAPPDATA%\\Forecast\\settings.json``.

    Matches ``paper-gui/forecast/models.py``'s ``data_dir()``/``settings_path()`` exactly; this is
    a read-only mirror of that path, not a second definition of where the launcher's data lives.
    """
    return _data_dir() / "settings.json"


def shared_state_path() -> Path:
    """Where Forecast keeps its install-state bookkeeping -- ``...\\Forecast\\state.json``.

    Matches ``paper-gui/forecast/models.py``'s ``state_path()`` exactly, for the same reason
    ``shared_settings_path`` matches ``settings_path()``.
    """
    return _data_dir() / "state.json"


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


def _installed_root(app_id: str, rec: dict[str, Any]) -> Path | None:
    """The install directory Forecast recorded for this module, if any is still on disk.

    An installer-kind module is owned by its own setup program, so the launcher only ever has
    ``location`` to go by; every other module -- including one, like PotreeDesktop, whose payload
    is just a folder Forecast copies verbatim rather than a built exe -- is a versioned payload the
    launcher unpacked itself, under ``apps/<id>/<active>``.
    """
    kind = rec.get("kind") or (rec.get("spec") or {}).get("kind")
    if kind == "installer":
        location = rec.get("location")
        root = Path(location) if location else None
    else:
        active = rec.get("active")
        root = (_data_dir() / "apps" / app_id / active) if active else None
    return root if (root is not None and root.is_dir()) else None


def _app_record(app_id: str) -> dict[str, Any] | None:
    state = _read_json(shared_state_path())
    rec = (state.get("apps") or {}).get(app_id)
    return rec if isinstance(rec, dict) else None


def resolve_app_root(app_id: str) -> str | None:
    """The install directory Forecast last recorded for ``app_id``, or None.

    For a module whose callers need the whole folder rather than one named exe inside it --
    PotreeDesktop being the example in this family, which is a folder of html/js Forecast installs
    verbatim and whose own launcher already knows how to find the right exe inside it by name.
    ``resolve_app_path`` is what a caller wants instead when it just needs to spawn the module.
    """
    rec = _app_record(app_id)
    if rec is None:
        return None
    root = _installed_root(app_id, rec)
    return str(root) if root is not None else None


def resolve_app_path(app_id: str) -> str | None:
    """Where the launcher's own ``forecast.launcher.resolve_exe`` would find this module's exe.

    Mirrors that function without importing it (which would pull in PyQt6's ``QProcess`` for a
    plain path lookup): the module's manifest-declared, payload-relative ``exe`` joined onto
    ``resolve_app_root``'s install directory. None when Forecast has never installed this module,
    or the exe it recorded is missing from disk.

    Like ``resolve_mode``/``resolve_language``, this only ever reads what the launcher already
    knows; nothing here searches the disk for a guessed install location -- a caller with its own
    fallback search (for a machine with no launcher at all) keeps it.
    """
    rec = _app_record(app_id)
    if rec is None:
        return None
    exe = str((rec.get("spec") or {}).get("exe") or "")
    root = _installed_root(app_id, rec)
    if not exe or root is None:
        return None
    path = root / exe
    return str(path) if path.is_file() else None
