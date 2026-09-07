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
def test_pill_radius_is_no_more_than_half_the_rendered_height(metrics):
    """A radius past half the widget's height silently falls back to square corners.

    Qt does not clamp an oversized radius to a capsule, so a pill radius has to be measured
    against the padding and font beside it. The estimate here is deliberately generous -- it
    catches a radius carried over from another density, not a one-pixel miss.
    """
    for pad, radius in ((metrics.pill_pad, metrics.pill_radius),
                        (metrics.chip_pad, metrics.chip_radius)):
        line_px = metrics.font_pt * 96 / 72 * 1.4
        height = pad[0] * 2 + 2 + line_px
        assert radius <= height / 2 + 1, (
            f"radius {radius} exceeds half of the ~{height:.0f}px rendered height")


@pytest.mark.parametrize("metrics", PRESETS, ids=lambda m: f"{m.font_pt}pt")
def test_secondary_tier_stays_below_the_body_tier(metrics):
    assert metrics.small_pt < metrics.font_pt
    assert metrics.font_pt < metrics.section_pt < metrics.title_pt
