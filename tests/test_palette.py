"""The palette as a value: parity, immutability, and the role tables."""

from __future__ import annotations

import pytest
from conftest import BOTH, TILE_STATES

import paperskin


def test_both_palettes_define_every_token():
    """A frozen dataclass with no defaults makes a missing token a ``TypeError`` at import rather
    than a colour that silently comes out empty. This asserts the property rather than trusting
    it."""
    for name in paperskin.token_names():
        assert getattr(paperskin.LIGHT, name) is not None, f"LIGHT.{name} is None"
        assert getattr(paperskin.DARK, name) is not None, f"DARK.{name} is None"


def test_palettes_are_not_a_copy_of_each_other():
    """Guards against a mode added by copy-paste.

    A handful of tokens are genuinely mode-independent -- the accent as a fill, the switch's "on"
    track, the decorative rule -- so this checks the proportion rather than demanding every token
    differ.
    """
    shared = [n for n in paperskin.token_names()
              if str(getattr(paperskin.LIGHT, n)) == str(getattr(paperskin.DARK, n))]
    assert len(shared) < len(paperskin.token_names()) // 3, f"suspiciously shared: {shared}"


def test_palette_is_hashable():
    """Frozen and slotted so a palette can be a QPixmap cache key -- which is how a cached static
    layer gets invalidated on a theme change without anyone remembering to invalidate it."""
    assert hash(paperskin.LIGHT) != hash(paperskin.DARK)
    assert len({paperskin.LIGHT, paperskin.DARK, paperskin.LIGHT}) == 2


@BOTH
def test_palette_is_immutable(pal):
    with pytest.raises((AttributeError, TypeError)):
        pal.accent = "#000000"


@BOTH
def test_every_tone_resolves(pal):
    for tone in paperskin.Tone:
        assert pal.tone(tone), f"{pal.name}: no colour for {tone}"


@BOTH
def test_unknown_tone_raises(pal):
    """Raises rather than falling back, so a typo in a severity or outcome table is a test failure
    instead of a label that silently comes out the wrong colour."""
    with pytest.raises(KeyError):
        pal.tone("nonsense")


@BOTH
def test_tone_value_is_the_qss_property_value(pal):
    """The enum value doubles as the ``[tone="..."]`` property value, so the selector and the
    Python that sets it cannot drift."""
    for tone in paperskin.Tone:
        assert isinstance(tone.value, str)
        assert tone.value == str(tone.value).lower()


@BOTH
def test_every_tile_state_has_its_own_colour(pal):
    colours = [pal.tile(state) for state in TILE_STATES]
    assert len(set(colours)) == len(TILE_STATES), "two tile states share a colour"


@BOTH
def test_unknown_tile_state_falls_back(pal):
    """Unlike ``tone()`` this falls back rather than raising: a tile map renders thousands of
    rectangles per frame and a new pipeline state should not crash the paint."""
    assert pal.tile("no-such-state") == pal.tile_pending


def test_ink_renders_both_forms():
    ink = paperskin.Ink(120, 92, 66, 0.18)
    assert str(ink) == "rgba(120, 92, 66, 0.18)"     # what QSS needs
    assert (ink.r, ink.g, ink.b) == (120, 92, 66)    # what a painter needs


def test_ink_defaults_to_opaque():
    assert str(paperskin.Ink(1, 2, 3)) == "rgba(1, 2, 3, 1.0)"


@pytest.mark.parametrize("mode, prefers_light, expected", [
    (paperskin.MODE_LIGHT, None, "light"),
    (paperskin.MODE_LIGHT, False, "light"),
    (paperskin.MODE_DARK, True, "dark"),
    (paperskin.MODE_DARK, None, "dark"),
    (paperskin.MODE_SYSTEM, True, "light"),
    (paperskin.MODE_SYSTEM, False, "dark"),
    (paperskin.MODE_SYSTEM, None, "dark"),
    ("garbage", None, "dark"),
])
def test_resolve(mode, prefers_light, expected):
    """Anything unrecognised is treated as system, and system with no answer resolves to dark -- so
    a dev run on a platform with no such preference looks as the app has always looked."""
    assert paperskin.resolve(mode, prefers_light=prefers_light).name == expected


def test_use_sets_the_active_palette():
    before = paperskin.active()
    try:
        assert paperskin.use(paperskin.LIGHT) is paperskin.LIGHT
        assert paperskin.active() is paperskin.LIGHT
        assert paperskin.use(paperskin.DARK) is paperskin.DARK
        assert paperskin.active() is paperskin.DARK
    finally:
        paperskin.use(before)


def test_modes_are_the_persisted_vocabulary():
    """One settings vocabulary across every app in the family."""
    assert paperskin.MODES == ("light", "dark", "system")
    assert paperskin.PALETTES == {"light": paperskin.LIGHT, "dark": paperskin.DARK}


def test_geometry_is_not_per_mode():
    """A radius is not an appearance, so it is a module constant rather than a palette field."""
    assert paperskin.RADIUS_PILL_LG == 20
    assert (paperskin.S1, paperskin.S7) == (4, 48)
    assert not any(n.startswith("radius") for n in paperskin.token_names())
