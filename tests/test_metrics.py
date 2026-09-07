"""The density axis.

Density is the one thing consuming apps legitimately differ on. It travels as a ``Metrics``
preset so that a full-screen operator window and a dense desktop tool still share every rule --
before this existed, papertrails restyled ``QPushButton`` in its own sheet, which is how its
buttons ended up a different shape from the other apps.
"""

from __future__ import annotations

import pytest

import forecast_theme
from forecast_theme import geometry

PRESETS = (geometry.COMPACT, geometry.COMFORTABLE)


@pytest.mark.parametrize("metrics", PRESETS, ids=lambda m: f"{m.font_pt}pt")
@pytest.mark.parametrize("pal", (forecast_theme.LIGHT, forecast_theme.DARK), ids=lambda p: p.name)
def test_every_preset_compiles(pal, metrics):
    qss = forecast_theme.base_qss(pal, metrics=metrics, glass=False)
    assert qss.count("{") == qss.count("}")
    assert "Ink(" not in qss and "None" not in qss
    assert f"font-size: {metrics.font_pt}pt" in qss
    for pad in (metrics.btn_pad, metrics.pill_pad, metrics.chip_pad):
        assert f"padding: {pad[0]}px {pad[1]}px" in qss


def test_density_changes_control_sizing():
    """The two presets must not compile to the same sheet, or density is not wired through."""
    compact = forecast_theme.base_qss(forecast_theme.DARK, metrics=geometry.COMPACT)
    comfortable = forecast_theme.base_qss(forecast_theme.DARK, metrics=geometry.COMFORTABLE)
    assert compact != comfortable


@pytest.mark.parametrize("metrics", PRESETS, ids=lambda m: f"{m.font_pt}pt")
def test_secondary_tier_stays_below_the_body_tier(metrics):
    assert metrics.small_pt < metrics.font_pt
    assert metrics.font_pt < metrics.section_pt < metrics.title_pt


@pytest.mark.parametrize("metrics", PRESETS, ids=lambda m: f"{m.font_pt}pt")
def test_plain_and_pill_buttons_share_a_height(metrics):
    """A primary and a secondary button side by side must be the same height.

    They differ only in horizontal padding and radius. paper-gui carried its own ``#Btn`` rule
    for years because the shared plain button was shorter than ``#Primary``.
    """
    assert metrics.btn_pad[0] == metrics.pill_pad[0]


def test_mismatched_button_padding_is_rejected():
    with pytest.raises(ValueError, match="same height|vertical padding"):
        geometry.Metrics(font_pt=10, small_pt=9, btn_pad=(6, 14), pill_pad=(9, 26),
                         pill_radius=20, pill_height=40, chip_pad=(4, 13),
                         chip_radius=14, chip_height=28)


@pytest.mark.parametrize("metrics", PRESETS, ids=lambda m: f"{m.font_pt}pt")
def test_pill_radii_are_at_most_half_the_measured_height(metrics):
    """Qt squares the corners rather than clamping, so a radius may never exceed half."""
    assert metrics.pill_radius <= metrics.pill_height // 2
    assert metrics.chip_radius <= metrics.chip_height // 2


def test_an_oversized_radius_is_rejected():
    with pytest.raises(ValueError, match="square corners"):
        geometry.Metrics(font_pt=18, small_pt=14, btn_pad=(14, 26), pill_pad=(14, 34),
                         pill_radius=32, pill_height=66, chip_pad=(8, 22),
                         chip_radius=24, chip_height=46)
