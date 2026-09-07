"""The accessibility promises the design makes.

Kept as tests rather than as comments in ``palette.py`` so that a palette edit has to face them.
"""

from __future__ import annotations

from conftest import BOTH

from forecast_theme import testing
from forecast_theme.derive import alpha, ink_on, mix


@BOTH
def test_readable_tiers_clear_aa_on_every_surface(pal):
    testing.assert_readable_tiers(pal)


@BOTH
def test_ink_on_filled_controls(pal):
    """A solid accent or danger fill has to carry the ink a consumer puts on it.

    ``ink_on()`` is what a consumer calls for exactly this -- the design's original hardcoded
    white on the accent button would have been 2.06:1, which is the mistake this guards.
    """
    assert testing.contrast(ink_on(pal.accent), pal.accent) >= testing.AA_NORMAL
    assert testing.contrast(ink_on(pal.danger), pal.danger) >= testing.AA_NORMAL


@BOTH
def test_selection_background_carries_text(pal):
    """The sheet sets ``selection-color: text`` over a computed ``accent_dim`` fill (``accent``
    mixed most of the way toward ``surface``)."""
    accent_dim = mix(pal.accent, pal.surface, 0.75)
    assert testing.contrast(pal.text, accent_dim) >= testing.AA_NORMAL


@BOTH
def test_rgb_accepts_every_form(pal):
    """A surface already resolved by ``surfaces()`` must feed back into ``over()``/``contrast()``.

    Without the tuple passthrough an app checking its own tokens against its own surfaces has to
    unpack them first, which is exactly the friction that makes people skip the check.
    """
    surface = testing.surfaces(pal)["surface"]
    assert testing.rgb(surface) == surface
    ink = alpha(pal.accent, 0.3)
    assert testing.rgb(ink) == (ink.r, ink.g, ink.b)
    assert testing.rgb(pal.text) == testing.rgb(pal.text.upper())


@BOTH
def test_over_respects_alpha(pal):
    """Compositing is the whole reason a derived fill's alpha can be tuned at all."""
    opaque = testing.Ink(255, 0, 0, 1.0)
    invisible = testing.Ink(255, 0, 0, 0.0)
    ground = (10, 20, 30)
    assert testing.over(opaque, ground) == (255, 0, 0)
    assert testing.over(invisible, ground) == ground


def test_contrast_is_symmetric_and_bounded():
    assert testing.contrast("#000000", "#ffffff") == testing.contrast("#ffffff", "#000000")
    assert round(testing.contrast("#000000", "#ffffff"), 1) == 21.0
    assert testing.contrast("#123456", "#123456") == 1.0
