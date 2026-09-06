"""The accessibility promises the design makes.

Kept as tests rather than as comments in ``palette.py`` so that a palette edit has to face them.
The ratios quoted in the palette's own comments are measured against the resolved composite of the
glass tokens over that mode's ground, which is what the operator actually sees -- and
``surfaces()`` recomputes that rather than hardcoding it, so tuning an alpha cannot silently
invalidate the numbers the design is checked against.
"""

from __future__ import annotations

from conftest import BOTH, TILE_STATES

from forecast_theme import testing


@BOTH
def test_readable_tiers_clear_aa_on_every_surface(pal):
    testing.assert_readable_tiers(pal)


@BOTH
def test_decorative_tiers_clear_three_to_one(pal):
    testing.assert_decorative_tiers(pal)


@BOTH
def test_tinted_fills_carry_their_ink(pal):
    testing.assert_tinted_fills(pal)


@BOTH
def test_ink_on_filled_controls(pal):
    """A solid accent or danger fill has to carry the ink the sheet puts on it.

    ``pill_ink`` on the accent is the primary action; the design's original white would have been
    2.06:1 there, which is the mistake this guards.
    """
    assert testing.contrast(pal.pill_ink, pal.accent) >= testing.AA_NORMAL
    assert testing.contrast(pal.danger_ink, pal.danger) >= testing.AA_NORMAL


@BOTH
def test_tile_grid_stays_visible_against_every_fill(pal):
    """No single hairline can hold 2:1 against a ramp that spans 35:1 by design, so this checks the
    *minimum* separation rather than a uniform one.

    The grid must never vanish entirely, which is what happened when it was drawn in the window
    background colour -- it became invisible exactly where it was the only thing saying the map had
    rendered.
    """
    worst = min(testing.contrast(pal.tile_grid_ink, pal.tile(state)) for state in TILE_STATES)
    assert worst > 1.05, f"{pal.name}: tile grid invisible somewhere ({worst:.3f}:1)"


@BOTH
def test_selection_background_carries_text(pal):
    """The sheet sets ``selection-color: text`` over ``selection-background-color: accent_dim``."""
    assert testing.contrast(pal.text, pal.accent_dim) >= testing.AA_NORMAL


@BOTH
def test_rgb_accepts_every_form(pal):
    """A surface already resolved by ``surfaces()`` must feed back into ``over()``/``contrast()``.

    Without the tuple passthrough an app checking its own tokens against its own surfaces has to
    unpack them first, which is exactly the friction that makes people skip the check.
    """
    card = testing.surfaces(pal)["card"]
    assert testing.rgb(card) == card
    assert testing.rgb(pal.glass) == (pal.glass.r, pal.glass.g, pal.glass.b)
    assert testing.rgb(pal.text) == testing.rgb(pal.text.upper())


@BOTH
def test_over_respects_alpha(pal):
    """Compositing is the whole reason the glass alphas can be tuned at all."""
    opaque = testing.Ink(255, 0, 0, 1.0)
    invisible = testing.Ink(255, 0, 0, 0.0)
    ground = (10, 20, 30)
    assert testing.over(opaque, ground) == (255, 0, 0)
    assert testing.over(invisible, ground) == ground


def test_contrast_is_symmetric_and_bounded():
    assert testing.contrast("#000000", "#ffffff") == testing.contrast("#ffffff", "#000000")
    assert round(testing.contrast("#000000", "#ffffff"), 1) == 21.0
    assert testing.contrast("#123456", "#123456") == 1.0
