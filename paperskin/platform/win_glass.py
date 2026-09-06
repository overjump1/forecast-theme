"""The native Windows appearance: the Windows 11 backdrop -- Mica -- the title bar, and the OS
light/dark preference.

This is what makes the window glass rather than a dark rectangle pretending to be glass. Mica
samples the desktop wallpaper behind the window and blurs it, so the app picks up the colour of
whatever the operator has behind it and reads as a physical pane.

Everything here is best-effort by design. ``DwmSetWindowAttribute`` returns a failure HRESULT
rather than raising on a build that does not know the attribute, transparency effects can be off
in Settings, and a remote session or VM may composite without backdrop support. So the caller is
told whether it worked and the stylesheet paints an opaque base when it did not -- see
``theme.qss(glass=...)``. A design that assumes the blur is there looks broken exactly where it is
least testable.

No dependency: ``ctypes`` against dwmapi, which is present on every Windows since Vista.
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

# DWM window attributes. The numbers are the contract; the names are for us.
DWMWA_USE_IMMERSIVE_DARK_MODE = 20      # dark title bar and frame
DWMWA_SYSTEMBACKDROP_TYPE = 38          # Windows 11 22H2+
DWMWA_MICA_EFFECT_UNDOCUMENTED = 1029   # Windows 11 21H2 only, before 38 existed

# Values for DWMWA_SYSTEMBACKDROP_TYPE.
BACKDROP_AUTO = 0
BACKDROP_NONE = 1
BACKDROP_MICA = 2            # what an application window is supposed to use
BACKDROP_ACRYLIC = 3         # heavier blur, meant for transient surfaces like flyouts
BACKDROP_MICA_ALT = 4        # "tabbed"; a warmer, higher-contrast Mica


def is_supported() -> bool:
    """True when this is a Windows build that could plausibly have a backdrop."""
    if sys.platform != "win32":
        return False
    return sys.getwindowsversion().build >= 22000       # Windows 11


def _set(hwnd: int, attribute: int, value: int) -> bool:
    """One DwmSetWindowAttribute call. True when DWM accepted it."""
    try:
        dwm = ctypes.windll.dwmapi
    except (AttributeError, OSError):
        return False
    payload = ctypes.c_int(value)
    try:
        result = dwm.DwmSetWindowAttribute(
            wintypes.HWND(hwnd),
            wintypes.DWORD(attribute),
            ctypes.byref(payload),
            ctypes.sizeof(payload),
        )
    except (OSError, ctypes.ArgumentError):
        return False
    return result == 0                                   # S_OK


def apply(hwnd: int, *, dark: bool, backdrop: int = BACKDROP_MICA) -> bool:
    """Match the window frame and backdrop to the active palette.

    ``dark`` has to be passed; there is deliberately no default. It used to be hardcoded to 1,
    which was invisible while there was only one palette and wrong the moment a light one existed.

    It also does more than the title bar. **Mica's tint follows this attribute, not the OS theme**,
    so ``dark=False`` is what produces a light backdrop for the window -- which means this has to
    be re-applied on a theme change, not only at startup, or the light palette's translucent fills
    end up compositing over a dark blur.

    Args:
        hwnd: The native window handle. Must already exist -- call this after ``show()`` or
            ``winId()``, because Qt creates the handle lazily and a call before that silently
            does nothing.
        dark: Whether the active palette is the dark one.
        backdrop: One of the ``BACKDROP_*`` values.

    Returns:
        True when the backdrop was accepted, which is the caller's cue that the window may be
        transparent. The frame attribute is applied either way: it is independent of the blur, and
        a frame that contradicts the app's palette is worse than no blur.
    """
    if not hwnd or sys.platform != "win32":
        return False

    # Applied first and unconditionally. On Windows 10 this is the only one that will land.
    _set(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, 1 if dark else 0)

    if not is_supported():
        return False

    if _set(hwnd, DWMWA_SYSTEMBACKDROP_TYPE, backdrop):
        return True

    # Windows 11 21H2 predates attribute 38 and only understands the undocumented flag.
    return _set(hwnd, DWMWA_MICA_EFFECT_UNDOCUMENTED, 1)


def transparency_enabled() -> bool:
    """Whether the user has "Transparency effects" switched on in Settings.

    Mica is silently ignored when this is off, and the window would come back a flat solid colour
    with no error anywhere. Checking lets the app choose the opaque stylesheet up front instead of
    rendering a design whose whole premise has been turned off.
    """
    if sys.platform != "win32":
        return False
    try:
        import winreg
    except ImportError:
        return False
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        ) as key:
            return bool(winreg.QueryValueEx(key, "EnableTransparency")[0])
    except OSError:
        # The value is absent on some builds, where transparency is on by default.
        return True


def system_prefers_light() -> bool | None:
    """The OS light/dark preference for applications, or None when it cannot be known.

    None rather than a bool, and this is the difference from ``transparency_enabled()``: a missing
    ``EnableTransparency`` genuinely means "on", but there is no defensible platform-level default
    for an appearance. What to do with "unknown" is theme policy, so it is ``theme.resolve``'s
    decision, not this module's.

    Qt exposes the same preference through ``QStyleHints.colorScheme()`` and that is what the app
    asks first -- but it reports ``Unknown`` under the offscreen platform plugin, which is what the
    build smoke test and CI run on. This is the fallback for that case.
    """
    if sys.platform != "win32":
        return None
    try:
        import winreg
    except ImportError:
        return None
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        ) as key:
            return bool(winreg.QueryValueEx(key, "AppsUseLightTheme")[0])
    except OSError:
        return None


def available() -> bool:
    """Whether to build the UI expecting glass, decided before any window exists."""
    return is_supported() and transparency_enabled()
