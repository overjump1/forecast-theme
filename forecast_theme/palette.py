"""The palette: design tokens as a value.

The palette is **hypsometric** -- borrowed from the elevation tinting a surveyor already reads on
every terrain map, rather than from software convention. Apricot-turned-sky-blue is the instrument
colour and means "active"; green means complete; gold means a warning; red means failed.

Two rules govern this module; the stylesheet's own rules live in ``sheet.py``, and every derived
tint (hovers, translucent fills, the ink that reads on a solid accent) lives in ``derive.py``.

1. **Two palettes, one vocabulary -- and the palette is a value, not a set of module globals.**
   ``LIGHT`` and ``DARK`` are two instances of one frozen ``Palette``, so a token missing from
   either is a ``TypeError`` at import rather than a colour that silently comes out empty. Paint
   code calls ``active()``; ``sheet.base_qss()`` is handed a palette explicitly so the selftest can
   compile every combination without touching global state.

2. **This module stays Qt-free.** The only Qt in it is a function-local import inside ``qc()``.
   That is what lets the contrast suite run headless in any consumer's CI.

**Why this palette is this small.** Earlier revisions of this file stored ~60 fields per mode --
glass/edge/fill/hover/pressed/overlay variants, a data-viz tile ramp, switch track/knob colours --
so that every derived tint was a name a consumer could reach for directly. That made the package
hard to actually share: a new consumer had to adopt the whole vocabulary or none of it, and half
the fields were really one core colour at a different alpha. The core below is the actual design
decision -- the ground, the surface, the hairline ink, the two text tiers, the accent and its ink,
and the three status colours. Everything else a stylesheet needs is computed from these by
``derive.alpha()``/``derive.mix()``/``derive.ink_on()`` at the point of use. Anything that is not a
generic UI colour at all -- algo-gui's tile-state ramp is the example -- does not belong here even
in derived form; it lives in the app that actually draws it, computed from these same core tokens.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum

# ---------------------------------------------------------------------------- appearance modes
#
# The persisted setting, not a palette. Named MODE_* rather than LIGHT/DARK because in this module
# ``LIGHT`` is a Palette -- the original app had ``theme.LIGHT`` (a Palette) and ``schema.LIGHT``
# (the string "light") live at once, which is a trap worth not re-exporting.
MODE_LIGHT = "light"
MODE_DARK = "dark"
MODE_SYSTEM = "system"
MODES = (MODE_LIGHT, MODE_DARK, MODE_SYSTEM)


class Tone(str, Enum):
    """A semantic colour role.

    The value doubles as the QSS dynamic-property value, so a ``[tone="warn"]`` selector and the
    Python that sets it cannot drift. This exists because a label whose colour is set with an
    inline ``setStyleSheet`` can never be re-themed -- so severity and outcome colours are carried
    as a property the stylesheet reads instead.
    """

    ACCENT = "accent"
    OK = "ok"
    WARN = "warn"
    DANGER = "danger"
    TEXT = "text"
    DIM = "dim"
    FAINT = "faint"


@dataclass(frozen=True, slots=True)
class Ink:
    """A translucent colour, stored once as channels and rendered into either form on demand.

    Necessary because the two consumers disagree: QSS wants ``rgba(r, g, b, a)`` and ``QColor``
    will not parse that string. ``__str__`` returns the CSS form so every f-string in ``sheet.py``
    works unchanged, and ``qc()`` covers the painters.
    """

    r: int
    g: int
    b: int
    a: float = 1.0

    def __str__(self) -> str:
        return f"rgba({self.r}, {self.g}, {self.b}, {self.a})"


def qc(token: "str | Ink"):
    """A token as a ``QColor``, whichever form it is stored in.

    The import is function-local on purpose: this module is otherwise Qt-free, which is what lets
    the palette and its contrast be tested without a display.
    """
    from PyQt6.QtGui import QColor

    if isinstance(token, Ink):
        return QColor(token.r, token.g, token.b, round(token.a * 255))
    return QColor(token)


@dataclass(frozen=True, slots=True)
class Palette:
    """One appearance -- the minimal, mode-dependent core every consumer shares.

    Frozen and slotted, with only ``str``/``bool`` fields, so a palette is hashable.
    """

    name: str
    dark: bool

    # ------------------------------------------------------------------ ground
    bg: str        # the window/page ground
    surface: str   # cards, popups, panels -- anything raised off the ground

    # ------------------------------------------------------------------ hairlines
    # A base ink for edges and dividers. Never used at full strength -- always through
    # ``derive.alpha()`` at whatever opacity the surface calls for, because a fixed grey border
    # goes muddy on one ground and invisible on the other, while ink-at-low-alpha reads on both.
    border: str

    # ------------------------------------------------------------------ accent
    accent: str
    # The ink for text/thin graphics set in the accent colour. Needed as its own token because
    # the accent is not always a safe ink over the page ground: in dark mode this is the accent
    # itself; in light mode the raw accent is under 2:1 as a foreground, so this is a deeper shade
    # instead. ``derive.ink_on()`` covers the *other* case -- an ink that sits on a solid accent
    # fill rather than on the page ground.
    accent_ink: str

    # ------------------------------------------------------------------ the ramp
    ok: str
    warn: str
    danger: str

    # ------------------------------------------------------------------ text
    text: str
    text_dim: str

    # ------------------------------------------------------------------ role aliases
    #
    # One vocabulary for the paintEvents and the log model, which think in roles rather than in
    # ramp names.

    def tone(self, tone: Tone) -> str:
        """Resolve a semantic role.

        Raises rather than falling back, so a typo in a ``Severity``/``Outcome`` table is a test
        failure instead of a label that silently comes out the wrong colour.
        """
        try:
            return {
                Tone.ACCENT: self.accent_ink,
                Tone.OK: self.ok,
                Tone.WARN: self.warn,
                Tone.DANGER: self.danger,
                Tone.TEXT: self.text,
                Tone.DIM: self.text_dim,
                # No separate faint tier in the minimal core; a caller that wants something
                # fainter than text_dim reaches for derive.alpha(pal.text_dim, ...) directly.
                Tone.FAINT: self.text_dim,
            }[Tone(tone)]
        except (KeyError, ValueError) as exc:
            raise KeyError(f"no colour for tone {tone!r}") from exc


# ---------------------------------------------------------------------------- the palettes
#
# Contrast is a promise this file makes and tests/test_contrast.py checks: text and status
# colours clear 4.5:1 on both the ground and the surface.

LIGHT = Palette(
    name=MODE_LIGHT,
    dark=False,

    bg="#EEF2F8",
    surface="#FFFFFF",

    border="#182D4C",

    accent="#0EA5E9",
    accent_ink="#075985",

    ok="#166534",
    warn="#854D0E",
    danger="#BE123C",

    text="#0F1B2D",
    text_dim="#47576D",
)

DARK = Palette(
    name=MODE_DARK,
    dark=True,

    bg="#0B0F16",
    surface="#131926",

    border="#C6D8F4",

    accent="#38BDF8",
    accent_ink="#38BDF8",

    ok="#4ADE80",
    warn="#FACC15",
    danger="#FB7185",

    text="#E8EFF9",
    text_dim="#9FB0C7",
)

PALETTES = {LIGHT.name: LIGHT, DARK.name: DARK}

# Starting value, so an import-order accident yields the appearance the app has always had rather
# than a half-applied one.
_active: Palette = DARK


def active() -> Palette:
    """The palette in force.

    For ``paintEvent`` and anywhere else a palette cannot be threaded in as an argument. Read at
    call time, never captured at import -- a module-level dict of colours taken from this is the
    one mistake that survives a theme change and even a window rebuild.
    """
    return _active


def use(pal: Palette) -> Palette:
    """Make ``pal`` the active palette. Returns it, so callers can chain."""
    global _active
    _active = pal
    return _active


def resolve(mode: str, *, prefers_light: bool | None) -> Palette:
    """The palette for an appearance mode.

    ``prefers_light`` is the OS preference, passed in rather than probed here: this module is
    Qt-free and registry-free, and threading the probe through is what makes every branch a real
    code path that a test can force.

    Args:
        mode: One of ``MODES``. Anything unrecognised is treated as ``system``.
        prefers_light: True or False from the OS, or None when it cannot be known.

    Returns:
        ``LIGHT`` or ``DARK``. ``None`` resolves to dark, so a dev run on another platform looks
        exactly as the app has always looked.
    """
    if mode == MODE_LIGHT:
        return LIGHT
    if mode == MODE_DARK:
        return DARK
    return LIGHT if prefers_light else DARK


def token_names() -> tuple[str, ...]:
    """Every field name on ``Palette``. Used by the parity and contrast tests."""
    return tuple(f.name for f in fields(Palette))
