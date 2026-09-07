"""Fonts, and the seam between the palette and the platform.

This is the only module that knows about both the palette and ``platform.win_glass``, which is what
lets ``palette.py`` stay Qt-free and registry-free while still resolving a "follow the system" mode.

It is its own module for two reasons that are not cosmetic:

- ``load_fonts()`` must be called once per process, not once per restyle. It used to live inside an
  ``apply_theme()`` that re-registered every bundled ``.ttf`` with ``QFontDatabase`` on each call.
  That was harmless while it happened twice per process; a theme switch that restyles in place
  would have made it once per click.

- A main window has to be able to rebuild the stylesheet when the appearance changes, and it
  cannot import the app's entry-point module -- that module imports the window.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontDatabase, QGuiApplication
from PyQt6.QtWidgets import QApplication, QWidget

from . import geometry, palette, sheet
from .platform import win_glass

# Three faces, three jobs. Every candidate list ends in something Windows always has, because a
# missing font is not an error the operator can act on.
#
# Hebrew is the constraint that picks these: the field of modern Hebrew-capable faces is small, and
# Heebo and Rubik are the two with real Hebrew design rather than Latin shapes with Hebrew bolted
# on. Both are bundled as variable fonts, and Qt 6.11 interpolates their weight axis properly --
# verified, because a variable font whose weights collapse to one would silently flatten the whole
# type hierarchy.
_SANS = ("Heebo", "Alef", "Segoe UI", "Arial", "Tahoma")
_DISPLAY = ("Rubik", "Heebo", "Alef", "Segoe UI", "Arial")
_MONO = ("JetBrains Mono", "Consolas", "Courier New")


class Faces:
    """The resolved font families, so callers stop passing three strings around."""

    __slots__ = ("sans", "display", "mono")

    def __init__(self, sans: str, display: str, mono: str) -> None:
        self.sans = sans
        self.display = display
        self.mono = mono

    def __repr__(self) -> str:
        return f"Faces(sans={self.sans!r}, display={self.display!r}, mono={self.mono!r})"


def font_dir() -> Path:
    """Directory holding the bundled TTFs, in a source tree or a frozen bundle.

    ``importlib.resources`` is deliberately not used here. Under PyInstaller this package's ``.py``
    files live inside the PYZ archive, so ``files("forecast_theme")`` resolves to a path that
    either does not exist on disk or points at the build machine's source tree -- not at
    ``_MEIPASS`` where the collected data actually landed. Checking ``_MEIPASS`` first is the
    form that works in both modes.

    The package ships a PyInstaller hook (``forecast_theme/__pyinstaller``) that collects this
    directory automatically, so a consuming app's ``.spec`` needs no fonts entry of its own.
    """
    base = getattr(sys, "_MEIPASS", None)
    if base:
        bundled = Path(base) / "forecast_theme" / "fonts"
        if bundled.is_dir():
            return bundled
    return Path(__file__).resolve().parent / "fonts"


def load_fonts(*, extra_dirs: Sequence[Path] = ()) -> Faces:
    """Register the bundled faces and resolve each role against what is actually available.

    Call once per process. Registering the same file twice is not an error, but it is not free
    either, and there is no reason to do it.

    Args:
        extra_dirs: Additional directories of ``.ttf`` files to register before resolving. An
            escape hatch for an app that must keep a face of its own; prefer not to use it, since a
            face only one app has is a face the shared design does not actually specify.
    """
    for directory in (font_dir(), *extra_dirs):
        if directory.is_dir():
            for path in sorted(directory.glob("*.ttf")):
                QFontDatabase.addApplicationFont(str(path))
    families = set(QFontDatabase.families())
    return Faces(_first(_SANS, families), _first(_DISPLAY, families), _first(_MONO, families))


def _first(candidates: Sequence[str], families: set[str]) -> str:
    for name in candidates:
        if name in families:
            return name
    return candidates[-1]


def system_prefers_light() -> bool | None:
    """The OS appearance preference, or None when it cannot be known.

    The registry is asked first and Qt second, which is the opposite of what you would expect and
    is deliberate. ``apply()`` calls ``setColorScheme()`` so that native dialogs follow the app, and
    that makes ``QStyleHints.colorScheme()`` report back *our* choice rather than the operating
    system's. Reading the registry first keeps "what does the OS want" and "what did we ask for"
    from becoming the same question.

    Qt remains the fallback for a platform with no such registry key, and its
    ``colorSchemeChanged`` signal is still the right way to be *told* the OS changed -- just not
    the right way to ask what it changed to.
    """
    value = win_glass.system_prefers_light()
    if value is not None:
        return value

    app = QGuiApplication.instance()
    if app is None:
        return None
    scheme = app.styleHints().colorScheme()
    if scheme == Qt.ColorScheme.Light:
        return True
    if scheme == Qt.ColorScheme.Dark:
        return False
    return None


def resolve_theme(mode: str) -> palette.Palette:
    """The palette for an appearance mode, with the system preference probed here."""
    return palette.resolve(mode, prefers_light=system_prefers_light())


def apply(app: QApplication, faces: Faces, *, glass: bool, extra: str = "",
          metrics: geometry.Metrics = geometry.COMPACT) -> None:
    """Set the application font and the stylesheet for the active palette.

    Args:
        app: The application.
        faces: Already-resolved font families -- see ``load_fonts()``.
        glass: True when the native backdrop was accepted, so the window can be transparent. False
            paints an opaque base instead, which is the path a machine with transparency effects
            turned off takes -- and the path an app with its own opaque chrome should always take.
        extra: The app's own rules, appended after the base sheet. QSS is last-wins at equal
            specificity, so this can override a base rule as well as add to it.
        metrics: Control sizing -- ``COMPACT`` for a desktop tool, ``COMFORTABLE`` for a
            full-screen operator window. Also sets the application font size, so the base
            font and the stylesheet cannot drift apart.
    """
    pal = palette.active()
    app.setFont(QFont(faces.sans, metrics.font_pt))

    # Tell Qt which scheme we are in, so the things Qt draws for us -- the native file picker, a
    # QMessageBox's standard icons -- match the app instead of the desktop. Guarded because it
    # arrived in Qt 6.8 and a stale environment should degrade rather than crash.
    hints = app.styleHints()
    if hasattr(hints, "setColorScheme"):
        hints.setColorScheme(Qt.ColorScheme.Dark if pal.dark else Qt.ColorScheme.Light)

    base = sheet.base_qss(pal, faces.sans, faces.display, faces.mono, glass=glass,
                          metrics=metrics)
    app.setStyleSheet(f"{base}\n{extra}" if extra else base)


def set_tone(widget: QWidget, tone: palette.Tone | None) -> None:
    """Colour a widget by semantic role.

    The colour is carried as a dynamic property the stylesheet reads, not written as an inline
    stylesheet. An inline sheet outranks the application stylesheet permanently, so a widget
    coloured that way can never be re-themed -- which also means it can never follow a theme
    switch.
    """
    widget.setProperty("tone", tone.value if tone is not None else None)
    repolish(widget)


def repolish(widget: QWidget) -> None:
    """Make the stylesheet re-evaluate a widget after one of its dynamic properties changed.

    Qt does not re-run the selectors on a property change by itself, so a ``[tone="warn"]`` rule
    would keep the colour the widget was born with.
    """
    widget.style().unpolish(widget)
    widget.style().polish(widget)
