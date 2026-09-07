"""The non-Qt export: CSS custom properties and a JS module.

Checked because the failure mode is silent at the other end. A CSS ``var()`` that resolves to
nothing does not error -- it inherits, or falls back to black -- so a token missing from the
generated file shows up as a wrong colour in a 3D viewer rather than as an exception anywhere.
"""

from __future__ import annotations

import json
import re

from conftest import BOTH

import forecast_theme
from forecast_theme import export


def test_every_colour_token_is_exported():
    """Both modes carry every colour field. ``name`` and ``dark`` are not colours."""
    css = export.css_vars()
    expected = [f for f in forecast_theme.token_names() if f not in ("name", "dark")]
    for field in expected:
        prop = f"--ft-{field.replace('_', '-')}"
        # once per mode, plus the -rgb companion for each
        assert css.count(f"{prop}:") == 2, f"{prop} not exported for both modes"
        assert css.count(f"{prop}-rgb:") == 2, f"{prop}-rgb missing"


def test_both_modes_have_their_own_block():
    css = export.css_vars()
    assert ':root, :root[data-theme="dark"] {' in css
    assert ':root[data-theme="light"] {' in css
    # The renderer is handed a resolved mode, so "system" must never reach the stylesheet.
    assert "system" not in css
    assert "prefers-color-scheme" not in css


@BOTH
def test_css_values_match_the_palette(pal):
    css = export.css_vars()
    block = css.split(':root[data-theme="light"] {')[1] if not pal.dark \
        else css.split(':root, :root[data-theme="dark"] {')[1]
    block = block.split("}")[0]
    for field in ("accent", "text", "bg", "danger"):
        assert f"--ft-{field}: {getattr(pal, field)};" in block


def test_exported_core_tokens_are_solid_colours():
    """The minimal core has no translucent field left on ``Palette`` -- every hover/fill tint is
    computed by a consumer from these solid colours (``derive.alpha()``/``mix()`` on the Python
    side; an equivalent helper on the JS side), not exported pre-baked."""
    css = export.css_vars()
    for field in forecast_theme.token_names():
        if field in ("name", "dark"):
            continue
        prop = f"--ft-{field.replace('_', '-')}:"
        assert not re.search(prop + r"\s*rgba\(", css), f"{field} exported as a translucent value"


def test_js_module_carries_the_three_forms():
    js = export.js_module()
    body = json.loads(js.split("export const PALETTES = ", 1)[1].split(";\n", 1)[0])
    assert set(body) == {"light", "dark"}
    for mode, palette in body.items():
        entry = palette["accent"]
        assert set(entry) == {"hex", "int", "rgb", "a"}
        # int is what THREE.Color wants, and it has to agree with the hex
        assert entry["int"] == int(entry["hex"].lstrip("#"), 16)
        assert entry["rgb"] == [int(entry["hex"][i:i + 2], 16) for i in (1, 3, 5)]


def test_js_and_css_agree():
    """The two artifacts are generated from one palette; this asserts they stayed that way."""
    css = export.css_vars()
    js = json.loads(export.js_module().split("export const PALETTES = ", 1)[1].split(";\n", 1)[0])
    for mode, pal in (("light", forecast_theme.LIGHT), ("dark", forecast_theme.DARK)):
        r, g, b = js[mode]["accent"]["rgb"]
        assert f"--ft-accent-rgb: {r}, {g}, {b};" in css


def test_pill_radius_is_not_the_qt_number():
    """CSS clamps a radius at half the height; that Qt build does not.

    The Qt values are measured against a real rendered height, and copying them into CSS would
    make a capsule into a slightly-rounded rectangle. A comment in the generated file says so;
    this makes sure the value itself stays right.
    """
    css = export.css_vars()
    assert "--ft-radius-pill: 999px;" in css
    assert f"--ft-radius-panel: {forecast_theme.RADIUS_PANEL}px;" in css


def test_write_produces_both_files(tmp_path):
    written = export.write(tmp_path)
    assert len(written) == 2
    names = {p.name for p in tmp_path.iterdir()}
    assert names == {"theme.generated.css", "theme.generated.js"}
    for path in tmp_path.iterdir():
        assert "do not edit" in path.read_text(encoding="utf-8")


def test_export_needs_no_qt():
    """The generator runs in a plain interpreter -- it is part of the Qt-free core."""
    import pathlib
    import sys

    source = pathlib.Path(sys.modules["forecast_theme.export"].__file__).read_text(encoding="utf-8")
    assert not [l for l in source.splitlines() if l.startswith(("import PyQt6", "from PyQt6"))]
