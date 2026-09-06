"""The palette: design tokens as a value.

The palette is **hypsometric** -- borrowed from the elevation tinting a surveyor already reads on
every terrain map, rather than from software convention. Apricot is the instrument colour and means
"active"; lowland green means complete; gold means a warning; fired clay means failed. A LiDAR
operator recognises that ramp before reading a single word, and it is why the accent here is not
the blue that every dashboard defaults to.

Two rules govern this module; the stylesheet's own rules live in ``sheet.py``.

1. **Two palettes, one vocabulary -- and the palette is a value, not a set of module globals.**
   ``LIGHT`` and ``DARK`` are two instances of one frozen ``Palette``, so a token missing from
   either is a ``TypeError`` at import rather than a colour that silently comes out empty. An
   earlier design for this rebound the module's globals in a ``use()`` call; it was rejected
   because it cannot reach a dict that captured the *strings* at import time, because it would have
   to recompute every derived table by hand, and because it makes reading this file no longer tell
   you which names are live. Paint code calls ``active()``; ``sheet.base_qss()`` is handed a
   palette explicitly so the selftest can compile every combination without touching global state.

2. **This module stays Qt-free.** The only Qt in it is a function-local import inside ``qc()``.
   That is what lets the contrast suite run headless in any consumer's CI, and it is a promise of
   the package rather than an accident of the original app.

Three consequences of rule 1 that are easy to get wrong:

- **A hairline is drawn in the mode's ink, at an alpha low enough to read as a rule rather than a
  border.** The dark theme's white-at-low-alpha edge is not a portable idea: ``rgba(255,255,255,
  0.07)`` over the light ground resolves to a contrast ratio of 1.018, which is not faint but
  absent. So the light edges are warm taupe ink and the dark ones are warm bone.

- **``edge_top`` changes meaning between modes, not name.** In dark it is the Windows 11 lit top
  edge. On a near-white card a lit edge is physically impossible, so in light it becomes "the
  distinguished edge" -- a slightly heavier rule than ``edge``.

- **The accent works as an ink only in dark mode.** ``#E6A870`` on the light ground is 1.56:1. So
  anywhere the dark theme sets the accent as a foreground or a 1px border, light mode needs
  ``accent_ink`` (text) or ``accent_line`` (thin graphics, which must still clear WCAG 1.4.11's
  3:1). In dark mode both alias to ``accent`` and nothing changes. Decorative apricot rules, which
  assert nothing, keep the accent at full strength in both modes -- that is ``rule``.
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
    inline ``setStyleSheet`` can never be re-themed -- the inline sheet outranks the application
    stylesheet forever -- so severity and outcome colours are carried as a property the stylesheet
    reads instead.
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
    will not parse that string. ``__str__`` returns the CSS form so every f-string in ``qss()``
    works unchanged, and ``qc()`` covers the painters. Before this, the two translucent colours
    that painting code needed were simply hardcoded as integer literals in two paintEvents,
    invisible to any search for a token.
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
    """One appearance.

    Frozen and slotted, with only ``str``/``bool``/``Ink`` fields, so a palette is hashable and can
    go straight into a pixmap cache key -- which is how the tile map's static layer is invalidated
    on a theme change without anyone having to remember to invalidate it.
    """

    name: str
    dark: bool

    # ------------------------------------------------------------------ ground
    # Only visible when the native backdrop is unavailable; with Mica the desktop shows through
    # instead. DEPTH is for popups, which are separate native windows with no backdrop and so must
    # be solid -- and in light mode it floats *above* the card, so a tooltip over a card cannot
    # vanish into it.
    void: str
    depth: str

    # ------------------------------------------------------------------ glass
    # Panel fills. Alpha, not solid: these sit over the Mica backdrop and are the whole effect.
    #
    # The light alphas are ~0.92 rather than dark's ~0.74 because light Mica is not white -- DWM
    # tints toward the blurred wallpaper, and a dark wallpaper pulls it down hard. At 0.58 the
    # secondary text tier measures 2.48:1 over a dark wallpaper and 6.01:1 over a light one; at
    # 0.92 it is 5.35:1 to 6.19:1 and the design stops depending on the operator's desktop. Dark
    # mode can afford a low alpha because it has unlimited room above its ground; light mode is
    # pinned against an ink ceiling.
    glass: Ink
    glass_hi: Ink
    glass_low: Ink

    # ------------------------------------------------------------------ hairlines
    edge: Ink
    edge_faint: Ink
    edge_hi: Ink
    edge_top: Ink

    # ------------------------------------------------------------------ accent
    accent: str
    accent_hi: str
    accent_dim: str
    accent_ink: str
    accent_line: str
    # The accent as a *wash* rather than a fill or an ink: the resting background of a chip,
    # a notice strip, a selected row. Completes the fill triple that warn_fill/danger_fill
    # already formed -- its absence was the one real gap in the original palette.
    accent_fill: Ink
    pill_ink: str
    on_accent_disabled: Ink
    rule: "str | Ink"

    # ------------------------------------------------------------------ the ramp
    ok: str
    warn: str
    danger: str
    danger_hi: str
    danger_ink: str
    ok_fill: Ink
    warn_fill: Ink
    danger_fill: Ink

    # ------------------------------------------------------------------ text
    text: str
    text_dim: str
    text_faint: str

    # ------------------------------------------------------------------ control fills
    ctrl_hover: Ink
    ctrl_pressed: Ink
    ctrl_disabled: Ink
    well: Ink          # the unfilled part of a progress bar
    overlay: Ink       # scrollbar handle
    overlay_hi: Ink    # scrollbar handle, hovered

    # ------------------------------------------------------------------ the switch
    # The slide's toggle: apricot track and white knob when on, taupe track and dark knob when off.
    # Painted by ui.switch, not styled, because a knob that moves cannot be expressed in QSS.
    track_on: str
    track_off: str
    knob_on: str
    knob_off: str

    # ------------------------------------------------------------------ tiles
    # A real elevation ramp: unmeasured ground is warm neutral, the active tile is apricot,
    # finished ground is lowland green, and failure is fired clay. Read in order this is the same
    # sequence a hypsometric legend uses, which is why a failure cluster is legible as a patch.
    #
    # These are tuned for a map, not for text: thousands of ~6px rectangles whose minimum pairwise
    # separation is what matters (16.4 dE00 light, 17.6 dark). TILE_PENDING is deliberately not the
    # slide's #C5AA91 -- at that value the pending/running pair measured 14.6, inside the confusion
    # zone at this size.
    tile_empty: str
    tile_pending: str
    tile_queued: str
    tile_running: str
    tile_done: str
    tile_carried: str
    tile_failed: str
    tile_aborted: str

    # The hairline drawn BETWEEN tiles. Deliberately its own token: it is ink, not a background,
    # and an earlier revision used the window background colour for it -- which meant a change to
    # the window silently changed the grid. Chosen by maximising the *minimum* contrast across all
    # eight fills, because no single hairline can hold 2:1 against a ramp that spans 35:1 by
    # design.
    tile_grid_ink: str

    # ------------------------------------------------------------------ painted-only
    extent_ink: Ink    # the survey extent, drawn over the tile field
    plate: Ink         # the RAM chart's pane of glass

    # ------------------------------------------------------------------ role aliases
    #
    # One vocabulary for the paintEvents and the log model, which think in roles rather than in
    # ramp names. These were module-level dicts of colour strings before, which froze whichever
    # palette was active at import time.

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
                Tone.FAINT: self.text_faint,
            }[Tone(tone)]
        except (KeyError, ValueError) as exc:
            raise KeyError(f"no colour for tone {tone!r}") from exc

    def tile(self, state: str) -> str:
        """Colour for a ``TileState`` value, falling back to pending for an unknown state."""
        return {
            "empty": self.tile_empty,
            "pending": self.tile_pending,
            "queued": self.tile_queued,
            "running": self.tile_running,
            "done": self.tile_done,
            "carried_over": self.tile_carried,
            "failed": self.tile_failed,
            "aborted": self.tile_aborted,
        }.get(state, self.tile_pending)


# ---------------------------------------------------------------------------- the palettes
#
# Contrast is a promise this file makes and tests/test_theme.py checks: every readable text tier
# clears 4.5:1 on every surface it can land on, the faint tier and every thin accent graphic clear
# 3:1, and the tile grid stays visible against all eight fills. The numbers in the comments are
# measured against the resolved composite of the glass tokens over that mode's ground, which is
# what the operator actually sees.

LIGHT = Palette(
    name=MODE_LIGHT,
    dark=False,

    # The slide's warm sand, verbatim from its slide master.
    void="#F6DCC0",
    depth="#FFFBF5",

    # Lighter than the ground, same hue family as the ground -- a card has to read as an elevated
    # sand surface, not a different, greyer material sitting on top of it. Two earlier passes
    # missed that from opposite sides: 252/241/228 composited to near-white (#FBEFE1) and read as a
    # flat white panel; pulling it down toward 238/219/196 desaturated it enough to read as grey
    # next to the apricot accent instead of just darker sand.
    glass=Ink(250, 232, 205, 0.85),
    glass_hi=Ink(253, 240, 220, 0.88),
    glass_low=Ink(238, 213, 185, 0.90),

    # Ink, not light -- see the docstring. At 0.34 this composites to #CBB095 over the ground,
    # which is the slide's #C5AA91 taupe rule to within three units.
    edge=Ink(120, 92, 66, 0.18),
    edge_faint=Ink(120, 92, 66, 0.09),
    edge_hi=Ink(120, 92, 66, 0.34),
    edge_top=Ink(120, 92, 66, 0.30),

    accent="#E6A870",           # the slide's apricot, and a fill only
    accent_hi="#D9975C",        # hover moves toward the viewer: deeper on a light ground
    accent_dim="#F0C79C",
    accent_ink="#894E15",       # 5.03 ground / 5.87 card / 4.74 recessed
    accent_line="#A96626",      # 3.45 ground / 3.30 recessed -- clears 1.4.11
    accent_fill=Ink(230, 168, 112, 0.18),   # accent_ink on it: 4.62 over the card
    pill_ink="#3A2A1C",         # 6.68 on the accent; the slide's white would be 2.06
    on_accent_disabled=Ink(58, 42, 28, 0.45),
    rule="#E6A870",             # decorative, so full strength

    ok="#3F6B18",               # 4.78 / 5.66 / 4.57
    warn="#795609",             # 5.06 / 5.90 / 4.76 -- see the collision note below
    danger="#A83318",           # 5.05 / 5.98 / 4.83
    danger_hi="#BC3C1E",
    danger_ink="#FFF6EF",       # 6.24 on the danger fill; the one ink whose direction flips
    ok_fill=Ink(63, 107, 24, 0.10),
    warn_fill=Ink(121, 86, 9, 0.10),
    danger_fill=Ink(168, 51, 24, 0.10),

    text="#2E241C",             # 11.49 / 13.35 / 10.98
    text_dim="#6B5545",         # 5.29 / 6.15 / 4.98
    text_faint="#8A7462",       # 3.35 / 3.89 / 3.15

    ctrl_hover=Ink(246, 229, 208, 0.95),
    ctrl_pressed=Ink(233, 213, 190, 0.95),
    ctrl_disabled=Ink(238, 213, 185, 0.55),
    well=Ink(120, 92, 66, 0.12),
    overlay=Ink(120, 92, 66, 0.22),
    overlay_hi=Ink(120, 92, 66, 0.38),

    track_on="#E6A870",
    track_off="#C5AA91",        # the slide's taupe, verbatim
    knob_on="#FFFFFF",
    knob_off="#404040",         # 4.71 against the taupe track

    tile_empty="#F0E2D0",
    tile_pending="#B2A190",
    tile_queued="#9E7418",
    tile_running="#E08C3E",     # deepened: the accent itself is 1.56:1 on sand
    tile_done="#6E9A32",
    tile_carried="#B6C99A",
    tile_failed="#B93E22",
    tile_aborted="#8A7F92",     # the one off-hue: aborted is not a point on the terrain ramp
    tile_grid_ink="#2A2018",    # minimum 2.86 across the eight fills

    extent_ink=Ink(74, 54, 38, 0.38),
    plate=Ink(238, 216, 190, 0.86),
)

DARK = Palette(
    name=MODE_DARK,
    dark=True,

    # Warm black rather than the neutral or green-cast black a dark theme usually reaches for, so
    # the apricot reads as instrument light rather than as a colour floating on grey.
    void="#1A1613",
    depth="#221D17",

    glass=Ink(42, 35, 27, 0.74),
    glass_hi=Ink(56, 47, 37, 0.82),
    glass_low=Ink(20, 17, 14, 0.66),

    # Warm bone at low alpha reads as a lit edge over any backdrop dark Mica can produce, where a
    # fixed grey would go muddy over a dark wallpaper.
    edge=Ink(255, 244, 230, 0.09),
    edge_faint=Ink(255, 244, 230, 0.04),
    edge_hi=Ink(255, 244, 230, 0.20),
    edge_top=Ink(255, 246, 234, 0.13),

    accent="#E6A870",
    accent_hi="#F3BC8A",        # hover brightens on a dark ground
    accent_dim="#6B4A2E",
    accent_ink="#E6A870",       # 7.76 on the card: the accent is already a usable ink here
    accent_line="#E6A870",
    accent_fill=Ink(230, 168, 112, 0.13),   # a dark ground needs less wash to read
    pill_ink="#3A2A1C",
    on_accent_disabled=Ink(242, 231, 218, 0.45),
    rule=Ink(230, 168, 112, 0.55),   # damped: a full-strength 1px apricot rule outshouts its own
                                     # sections on a dark ground

    ok="#8FC154",               # 8.50 / 7.55 / 6.57
    warn="#EFD03B",             # 11.78 / 10.46 / 9.11
    danger="#E7745E",           # 6.04 / 5.42 / 4.72
    danger_hi="#EE8A75",
    danger_ink="#2C1008",       # 5.96 on the danger fill
    ok_fill=Ink(143, 193, 84, 0.13),
    warn_fill=Ink(239, 208, 59, 0.13),
    # 0.11, not the 0.13 its warn/ok siblings use: DANGER as an ink on its own fill is the
    # tightest pairing in either palette, and at 0.13 a #Error label inside a #BannerError
    # measured 4.47:1 -- a hair under AA, on the one message that most needs reading. Two
    # points of alpha buys 4.63:1 and is not perceptible as a tint change.
    danger_fill=Ink(231, 116, 94, 0.11),

    text="#F2E7DA",             # 14.74 / 13.09 / 11.40
    text_dim="#AD9C88",         # 6.75 / 6.00 / 5.28
    text_faint="#8F7E6D",       # 4.60 / 4.09 / 3.59

    ctrl_hover=Ink(74, 62, 49, 0.85),
    ctrl_pressed=Ink(26, 22, 18, 0.90),
    ctrl_disabled=Ink(20, 17, 14, 0.35),
    well=Ink(255, 244, 230, 0.07),
    overlay=Ink(255, 244, 230, 0.13),
    overlay_hi=Ink(255, 244, 230, 0.24),

    track_on="#E6A870",
    track_off="#4A4038",        # the slide's taupe would read as *on* against this ground
    knob_on="#FFFDF8",
    knob_off="#A08F7D",         # inverted: a dark knob on a dark track is invisible

    tile_empty="#1F1A15",
    tile_pending="#5A4E40",
    tile_queued="#856825",
    tile_running="#E6A870",
    tile_done="#8FC154",
    tile_carried="#40693A",
    # Deliberately redder than DANGER, which the other tiles' failed colour used to track. In a
    # warm palette the danger and accent hues are neighbours, so as a 6px square the failed tile
    # sat 19.0 dE00 from the running tile -- and running-versus-failed is the one confusion that
    # matters, since one is fine and the other needs someone. This is 24.9, matching light mode.
    tile_failed="#E05038",
    tile_aborted="#6A5A6E",
    tile_grid_ink="#3A312A",    # minimum 1.36; the old #0B1014 against the old empty was 1.05,
                                # i.e. the grid was invisible exactly where it was the only thing
                                # saying the map had rendered

    extent_ink=Ink(255, 244, 230, 0.30),
    plate=Ink(26, 22, 18, 0.62),
)

# WARN is the one token whose two values are not a lightness translation of each other, and that is
# deliberate. The old ochre (#D9A24B) sat 7.9 dE00 from the new apricot accent -- the same colour,
# at 9pt on a log line glanced at during a four-hour run. Warning has only three legible hues and
# the accent now owns amber and orange, so warning has to be yellow. Dark mode can be a *vivid*
# yellow: chroma 73 against the accent's 41, which is the axis that survives at 6px where hue
# discrimination degrades, for 20.5 dE00 of separation. Light mode cannot -- 4.5:1 on sand needs
# Y <= 0.119 and any legible yellow is Y ~ 0.5 -- so it takes its separation from lightness
# instead, at L* 41 against the accent's 73.5, for 30.7. Same idea in both: warning is the chip
# that steps furthest from the ground.

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
    code path that a test can force -- the same reasoning ``app.py`` gives for ``glass``.

    Args:
        mode: One of ``schema.THEMES``. Anything unrecognised is treated as ``system``, matching
            ``i18n.set_language``'s stance on a value it does not know.
        prefers_light: True or False from the OS, or None when it cannot be known -- a non-Windows
            machine, or a build without the registry value.

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
