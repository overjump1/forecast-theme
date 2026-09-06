"""The properties that only break once the package is installed rather than merely imported."""

from __future__ import annotations

import pathlib
import sys

import paperskin


def test_fonts_ship_with_the_package():
    """The failure this catches is silent.

    A font-less wheel degrades to a system fallback that nobody notices until a Hebrew screenshot
    -- which is why it is asserted rather than assumed. The equivalent check against a *frozen*
    bundle belongs in each consumer's build script, since only there does ``_MEIPASS`` exist.
    """
    from paperskin.styling import font_dir      # imports Qt, so keep it local to this test

    directory = font_dir()
    assert directory.is_dir(), f"no font directory at {directory}"
    faces = {p.stem for p in directory.glob("*.ttf")}
    for required in ("Heebo", "Rubik", "JetBrainsMono"):
        assert required in faces, f"{required}.ttf missing from {directory}"


def test_font_licences_ship_alongside_them():
    """These are SIL OFL faces; redistributing them without the licence is not permitted."""
    from paperskin.styling import font_dir

    assert list(font_dir().glob("OFL-*.txt")), "OFL licences missing from the package"


def test_public_surface_is_importable():
    for name in paperskin.__all__:
        assert hasattr(paperskin, name), f"__all__ promises {name} but it is missing"


def test_unknown_attribute_still_raises():
    """The lazy ``__getattr__`` must not swallow typos."""
    try:
        paperskin.no_such_thing
    except AttributeError:
        pass
    else:
        raise AssertionError("__getattr__ returned something for an unknown name")


def test_core_modules_are_qt_free():
    """``palette``/``geometry``/``sheet``/``testing`` import no Qt at module scope.

    That is what lets the contrast promises be checked in a headless CI job with no PyQt6 wheel,
    and it is a guarantee of the package rather than an accident of where the code came from.
    """
    for module in ("paperskin.palette", "paperskin.geometry", "paperskin.sheet",
                   "paperskin.testing"):
        __import__(module)
        source = pathlib.Path(sys.modules[module].__file__).read_text(encoding="utf-8")
        offenders = [line for line in source.splitlines()
                     if line.startswith(("import PyQt6", "from PyQt6"))]
        assert not offenders, f"{module} imports Qt at module scope: {offenders}"


def test_core_surface_works_without_pyqt6_installed():
    """The headless guarantee, proved rather than assumed.

    ``test_core_modules_are_qt_free`` only reads source text, and a machine that happens to have
    PyQt6 installed would pass it while the guarantee quietly rotted -- so this actually blocks the
    import and exercises the contrast suite and the stylesheet against it. That is the case a token
    generator or a CI contrast job runs in.
    """
    import importlib

    class Blocker:
        def find_module(self, name, path=None):
            if name.split(".")[0] == "PyQt6":
                return self

        def load_module(self, name):
            raise ImportError("PyQt6 blocked for this test")

    blocker = Blocker()
    saved = {k: v for k, v in sys.modules.items() if k.split(".")[0] in ("PyQt6", "paperskin")}
    for name in list(saved):
        del sys.modules[name]
    sys.meta_path.insert(0, blocker)
    try:
        ps = importlib.import_module("paperskin")
        for pal in (ps.LIGHT, ps.DARK):
            ps.testing.assert_readable_tiers(pal)
            ps.testing.assert_tinted_fills(pal)
            assert ps.base_qss(pal)
        try:
            ps.load_fonts()
        except ImportError:
            pass                    # the Qt surface must fail cleanly, not silently degrade
        else:
            raise AssertionError("load_fonts() worked with PyQt6 blocked")
    finally:
        sys.meta_path.remove(blocker)
        for name in list(sys.modules):
            if name.split(".")[0] in ("PyQt6", "paperskin"):
                del sys.modules[name]
        sys.modules.update(saved)


def test_pyinstaller_hook_is_discoverable():
    """Without this the fonts do not reach a frozen build, and see the docstring above for how
    quietly that fails."""
    from paperskin.__pyinstaller import get_hook_dirs

    dirs = [pathlib.Path(d) for d in get_hook_dirs()]
    assert dirs, "no hook dirs registered"
    assert any((d / "hook-paperskin.py").is_file() for d in dirs), (
        f"hook-paperskin.py not found in {dirs}")
