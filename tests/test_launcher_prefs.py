"""launcher_prefs: the shared, read-only mirror of the launcher's install-state.

Headless like the rest of the suite -- these functions only ever do os.environ/json/Path work, no
Qt involved.
"""

from __future__ import annotations

import json

from forecast_theme import launcher_prefs


def _set_data_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    return tmp_path / "Forecast"


def test_resolve_app_path_none_with_no_launcher_data(monkeypatch, tmp_path):
    _set_data_dir(monkeypatch, tmp_path)
    assert launcher_prefs.resolve_app_path("paperclip") is None
    assert launcher_prefs.resolve_app_root("paperclip") is None


def test_resolve_app_path_from_state_exe_kind(monkeypatch, tmp_path):
    data_dir = _set_data_dir(monkeypatch, tmp_path)
    exe = data_dir / "apps" / "potree" / "1.8.2" / "node_modules" / "electron" / "dist" / "electron.exe"
    exe.parent.mkdir(parents=True)
    exe.write_text("")
    data_dir.mkdir(exist_ok=True)
    (data_dir / "state.json").write_text(json.dumps({
        "schema": 1,
        "apps": {
            "potree": {
                "active": "1.8.2",
                "installed": ["1.8.2"],
                "kind": "exe",
                "spec": {"exe": "node_modules/electron/dist/electron.exe"},
            },
        },
    }))

    assert launcher_prefs.resolve_app_path("potree") == str(exe)
    # PotreeDesktop's own launcher needs the whole install folder, not the electron.exe buried
    # inside it -- it does its own exe-name search within that folder.
    assert launcher_prefs.resolve_app_root("potree") == str(exe.parents[3])


def test_resolve_app_path_from_state_installer_kind(monkeypatch, tmp_path):
    data_dir = _set_data_dir(monkeypatch, tmp_path)
    install_dir = tmp_path / "Program Files" / "algo_gui"
    exe = install_dir / "AlgoGui.exe"
    exe.parent.mkdir(parents=True)
    exe.write_text("")
    data_dir.mkdir(exist_ok=True)
    (data_dir / "state.json").write_text(json.dumps({
        "schema": 1,
        "apps": {
            "algorithms": {
                "active": "1.1.0",
                "installed": ["1.1.0"],
                "kind": "installer",
                "location": str(install_dir),
                "spec": {"exe": "AlgoGui.exe"},
            },
        },
    }))

    assert launcher_prefs.resolve_app_path("algorithms") == str(exe)
    assert launcher_prefs.resolve_app_root("algorithms") == str(install_dir)


def test_resolve_app_path_missing_exe_on_disk_is_none(monkeypatch, tmp_path):
    data_dir = _set_data_dir(monkeypatch, tmp_path)
    data_dir.mkdir(exist_ok=True)
    # state.json claims an active version, but nothing was actually unpacked there.
    (data_dir / "state.json").write_text(json.dumps({
        "schema": 1,
        "apps": {"paperclip": {"active": "1.0", "spec": {"exe": "paper-clip.exe"}}},
    }))

    assert launcher_prefs.resolve_app_path("paperclip") is None
    assert launcher_prefs.resolve_app_root("paperclip") is None


def test_resolve_app_path_unknown_app_is_none(monkeypatch, tmp_path):
    _set_data_dir(monkeypatch, tmp_path)
    assert launcher_prefs.resolve_app_path("nope") is None
    assert launcher_prefs.resolve_app_root("nope") is None
