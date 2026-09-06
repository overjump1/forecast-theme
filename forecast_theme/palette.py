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

    # A cool near-white, not a warm one. The ground is the single biggest decision in a palette:
    # everything else is read against it, and a neutral-cool ground is what lets the accent stay
    # a signal instead of competing with the paper.
    void="#EEF2F8",
    depth="#FFFFFF",

    # Cards are white over the cool ground. High alphas because light Mica tints toward the
    # wallpaper, and a dark desktop would otherwise drag the surface down with it.
    glass=Ink(255, 255, 255, 0.86),
    glass_hi=Ink(255, 255, 255, 0.94),
    glass_low=Ink(224, 232, 243, 0.92),

    # Hairlines are ink at low alpha, never a fixed grey: over a surface that shifts with the
    # backdrop, a fixed grey goes muddy in one direction and invisible in the other.
    edge=Ink(24, 45, 76, 0.16),
    edge_faint=Ink(24, 45, 76, 0.08),
    edge_hi=Ink(24, 45, 76, 0.30),
    edge_top=Ink(24, 45, 76, 0.26),

    accent="#0EA5E9",
    accent_hi="#0284C7",
    accent_dim="#BAE6FD",
    accent_ink="#075985",
    accent_line="#0369A1",
    accent_fill=Ink(14, 165, 233, 0.14),
    pill_ink="#032430",
    on_accent_disabled=Ink(3, 36, 48, 0.45),
    rule="#0EA5E9",

    ok="#166534",
    warn="#854D0E",
    danger="#BE123C",
    danger_hi="#9F1239",
    danger_ink="#FFF1F4",
    ok_fill=Ink(22, 101, 52, 0.10),
    warn_fill=Ink(133, 77, 14, 0.10),
    danger_fill=Ink(190, 18, 60, 0.10),

    text="#0F1B2D",
    text_dim="#47576D",
    text_faint="#68788F",

    ctrl_hover=Ink(234, 240, 249, 0.95),
    ctrl_pressed=Ink(213, 224, 239, 0.95),
    ctrl_disabled=Ink(224, 232, 243, 0.55),
    well=Ink(24, 45, 76, 0.12),
    overlay=Ink(24, 45, 76, 0.22),
    overlay_hi=Ink(24, 45, 76, 0.38),

    track_on="#0EA5E9",
    track_off="#A9B8CC",
    knob_on="#FFFFFF",
    knob_off="#39485C",

    tile_empty="#E2EAF4",
    tile_pending="#8F9FB5",
    tile_queued="#1D6A9B",
    tile_running="#0EA5E9",
    tile_done="#2E9E5B",
    tile_carried="#A4D6BA",
    tile_failed="#DC2E4E",
    tile_aborted="#8A84A6",
    tile_grid_ink="#16202C",

    extent_ink=Ink(15, 27, 45, 0.38),
    plate=Ink(224, 232, 243, 0.86),
)

DARK = Palette(
    name=MODE_DARK,
    dark=True,

    # Deep, cool and slightly blue rather than the neutral charcoal a dark theme usually reaches
    # for. It makes the cyan read as instrument light rather than as a colour floating on grey.
    void="#0B0F16",
    depth="#131926",

    glass=Ink(24, 31, 43, 0.74),
    glass_hi=Ink(35, 45, 60, 0.82),
    glass_low=Ink(9, 13, 19, 0.66),

    # Cool bone at low alpha, so the edge reads as lit over any backdrop dark Mica can produce.
    edge=Ink(198, 216, 244, 0.09),
    edge_faint=Ink(198, 216, 244, 0.04),
    edge_hi=Ink(198, 216, 244, 0.20),
    edge_top=Ink(210, 228, 255, 0.13),

    accent="#38BDF8",
    accent_hi="#7DD3FC",
    accent_dim="#1E4459",
    accent_ink="#38BDF8",
    accent_line="#38BDF8",
    accent_fill=Ink(56, 189, 248, 0.13),
    pill_ink="#03222E",
    on_accent_disabled=Ink(232, 239, 249, 0.45),
    rule=Ink(56, 189, 248, 0.55),

    ok="#4ADE80",
    warn="#FACC15",
    danger="#FB7185",
    danger_hi="#FDA4AF",
    danger_ink="#2B0A12",
    ok_fill=Ink(74, 222, 128, 0.13),
    warn_fill=Ink(250, 204, 21, 0.13),
    danger_fill=Ink(251, 113, 133, 0.11),

    text="#E8EFF9",
    text_dim="#9FB0C7",
    text_faint="#75879F",

    ctrl_hover=Ink(45, 58, 76, 0.85),
    ctrl_pressed=Ink(11, 15, 22, 0.90),
    ctrl_disabled=Ink(9, 13, 19, 0.35),
    well=Ink(198, 216, 244, 0.07),
    overlay=Ink(198, 216, 244, 0.13),
    overlay_hi=Ink(198, 216, 244, 0.24),

    track_on="#38BDF8",
    track_off="#3A4759",
    knob_on="#F8FBFF",
    knob_off="#93A5BC",

    # Cool-tuned, but still a real ramp: unmeasured ground is slate, the active tile is the accent,
    # finished ground is green, and failure is a red pushed away from the accent's hue so the
    # running/failed pair stays separable at 6px, which is the one confusion that matters.
    tile_empty="#121926",
    tile_pending="#46556A",
    tile_queued="#2A6F97",
    tile_running="#38BDF8",
    tile_done="#4ADE80",
    tile_carried="#2F7D53",
    tile_failed="#F43F5E",
    tile_aborted="#7A6E9B",
    tile_grid_ink="#2B3646",

    extent_ink=Ink(198, 216, 244, 0.30),
    plate=Ink(11, 15, 22, 0.62),
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
