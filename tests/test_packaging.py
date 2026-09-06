"""The properties that only break once the package is installed rather than merely imported."""

from __future__ import annotations

import pathlib
import sys

import forecast_theme


def test_fonts_ship_with_the_package():
    """The failure this catches is silent.

    A font-less wheel degrades to a system fallback that nobody notices until a Hebrew screenshot
    -- which is why it is asserted rather than assumed. The equivalent check against a *frozen*
    bundle belongs in each consumer's build script, since only there does ``_MEIPASS`` exist.
    """
    from forecast_theme.styling import font_dir      # imports Qt, so keep it local to this test

    directory = font_dir()
    assert directory.is_dir(), f"no font directory at {directory}"
    faces = {p.stem for p in directory.glob("*.ttf")}
    for required in ("Heebo", "Rubik", "JetBrainsMono"):
        assert required in faces, f"{required}.ttf missing from {directory}"


def test_font_licences_ship_alongside_them():
    """These are SIL OFL faces; redistributing them without the licence is not permitted."""
    from forecast_theme.styling import font_dir

    assert list(font_dir().glob("OFL-*.txt")), "OFL licences missing from the package"


def test_public_surface_is_importable():
    for name in forecast_theme.__all__:
        assert hasattr(forecast_theme, name), f"__all__ promises {name} but it is missing"


def test_unknown_attribute_still_raises():
    """The lazy ``__getattr__`` must not swallow typos."""
    try:
        forecast_theme.no_such_thing
    except AttributeError:
        pass
    else:
        raise AssertionError("__getattr__ returned something for an unknown name")


def test_core_modules_are_qt_free():
    """``palette``/``geometry``/``sheet``/``testing`` import no Qt at module scope.

    That is what lets the contrast promises be checked in a headless CI job with no PyQt6 wheel,
    and it is a guarantee of the package rather than an accident of where the code came from.
    """
    for module in ("forecast_theme.palette", "forecast_theme.geometry", "forecast_theme.sheet",
                   "forecast_theme.testing"):
        __import__(module)
        source = pathlib.Path(sys.modules[module].__file__).read_text(encoding="utf-8")
        offenders = [line for line in source.splitlines()
                     if line.startswith(("import PyQt6", "from PyQt6"))]
        assert not offenders, f"{module} imports Qt at module scope: {offenders}"


# Run in a subprocess, not in-process. Simulating Qt's absence by unloading it from an interpreter
# that has already imported it crashes with an access violation -- its C extension modules cannot
# be unloaded and re-imported. A fresh interpreter has not touched Qt yet, so blocking it there is
# both safe and a more faithful test of what this guards: a machine where PyQt6 is not installed.
_HEADLESS_PROBE = """
import sys

# A None in sys.modules makes `import PyQt6` raise ImportError -- documented behaviour, stable
# across versions, and it needs no meta_path finder. The first attempt used a find_module()-style
# finder, which Python 3.12 removed: the blocker went inert and the probe crashed instead of
# failing. Submodules are covered too, since importing PyQt6.QtGui imports PyQt6 first.
sys.modules["PyQt6"] = None

import forecast_theme as ps

for pal in (ps.LIGHT, ps.DARK):
    ps.testing.assert_readable_tiers(pal)
    ps.testing.assert_decorative_tiers(pal)
    ps.testing.assert_tinted_fills(pal)
    assert ps.base_qss(pal)
    assert ps.tone_rules(pal)

try:
    ps.load_fonts()
except ImportError:
    pass                     # the Qt surface must fail cleanly, not silently degrade
else:
    raise SystemExit("load_fonts() worked with PyQt6 blocked")

assert sys.modules["PyQt6"] is None, "importing forecast_theme pulled in Qt"
print("OK")
"""


def test_core_surface_works_without_pyqt6_installed():
    """The headless guarantee, proved rather than assumed.

    ``test_core_modules_are_qt_free`` only reads source text, and a machine that happens to have
    PyQt6 installed would pass it while the guarantee quietly rotted. This blocks the import for
    real and exercises the contrast suite and the stylesheet against it -- which is the case a
    token generator or a CI contrast job actually runs in.
    """
    import subprocess

    result = subprocess.run([sys.executable, "-c", _HEADLESS_PROBE],
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, (
        f"headless probe failed:\n{result.stdout}\n{result.stderr}")
    assert "OK" in result.stdout


def test_pyinstaller_hook_is_discoverable():
    """Without this the fonts do not reach a frozen build, and see the docstring above for how
    quietly that fails."""
    from forecast_theme.__pyinstaller import get_hook_dirs

    dirs = [pathlib.Path(d) for d in get_hook_dirs()]
    assert dirs, "no hook dirs registered"
    assert any((d / "hook-forecast_theme.py").is_file() for d in dirs), (
        f"hook-forecast_theme.py not found in {dirs}")
