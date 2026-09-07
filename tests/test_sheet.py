"""The stylesheet: it must compile, and it must contain no colour of its own."""

from __future__ import annotations

import inspect
import re

from conftest import BOTH

import forecast_theme
from forecast_theme import sheet, testing


@BOTH
def test_qss_compiles(pal):
    for glass in (True, False):
        text = forecast_theme.base_qss(pal, glass=glass)
        testing.check_qss(text)
        assert text.strip()


@BOTH
def test_glass_flag_changes_the_window_fill(pal):
    """``glass=False`` is the path a machine with transparency effects turned off takes, and the
    path an app with its own opaque chrome should always take. It has to look deliberate rather
    than broken, which means an opaque base rather than a missing one."""
    assert "QMainWindow { background: transparent; }" in forecast_theme.base_qss(pal, glass=True)
    assert f"QMainWindow {{ background: {pal.bg}; }}" in forecast_theme.base_qss(pal, glass=False)


@BOTH
def test_no_universal_widget_background(pal):
    """Rule 1. A ``QWidget { background: ... }`` rule makes glass impossible: every child widget
    paints itself opaque, so a translucent window has nothing to show through. Backgrounds are
    declared only on the surfaces meant to be surfaces."""
    text = forecast_theme.base_qss(pal)
    block = text.split("QWidget {", 1)[1].split("}", 1)[0]
    assert "background" not in block, "QWidget rule grew a background"


def test_qss_has_no_colour_literals():
    """The guard that keeps the hardcoded colours from creeping back.

    Every one that used to be there -- the scrollbar handle, the toggle track, the progress well,
    the primary button's ink -- was a dark-mode assumption, and converting only the paint sites
    would have shipped a light mode with invisible controls.

    Read from the live source rather than a hardcoded path, so splitting the module cannot quietly
    disable the check.
    """
    body = inspect.getsource(sheet.base_qss)
    code = "\n".join(l for l in body.splitlines() if not l.strip().startswith("#"))
    assert not re.findall(r"#[0-9A-Fa-f]{3,8}\b", code), "hex literal below def base_qss()"
    assert not re.findall(r"rgba?\(\s*\d", code), "rgba() literal below def base_qss()"


@BOTH
def test_tone_rules_out_specify_the_type_scale(pal):
    """Qt follows CSS2 specificity, so a bare ``QLabel[tone="ok"]`` loses to ``QLabel#Section`` and
    a toned headline would silently keep the type scale's colour. Hence one selector per host."""
    text = forecast_theme.base_qss(pal)
    hosts = [h for h in ("#Title", "#Section", "#Eyebrow", "#Dim", "#Faint", "#Error", "#Warn",
                         "#Mono") if f"QLabel{h}" in text]
    assert hosts, "the type scale vanished"
    for tone in forecast_theme.Tone:
        assert f'QLabel[tone="{tone.value}"]' in text, f"no bare rule for {tone.value}"
        for host in hosts:
            assert f'QLabel{host}[tone="{tone.value}"]' in text, (
                f"{host} would out-specify tone {tone.value}")


@BOTH
def test_tone_rules_accepts_app_hosts(pal):
    """An app whose own sheet colours ``QLabel#CardName`` must be able to cover it too -- this is
    the seam that stops the specificity trap being re-discovered per app."""
    extra = forecast_theme.tone_rules(pal, hosts=("#CardName", "#RowTitle"))
    for tone in forecast_theme.Tone:
        assert f'QLabel#CardName[tone="{tone.value}"]' in extra
        assert f'QLabel#RowTitle[tone="{tone.value}"]' in extra


@BOTH
def test_contract_names_are_all_styled(pal):
    """Every name the package promises to style must actually appear in the sheet."""
    text = forecast_theme.base_qss(pal)
    missing = [n for n in forecast_theme.CONTRACT_NAMES if f"#{n}" not in text]
    assert not missing, f"CONTRACT_NAMES not styled: {sorted(missing)}"


@BOTH
def test_app_specific_selectors_are_not_in_the_base_sheet(pal):
    """These belong to one app and were deliberately lifted out. If one comes back, the base sheet
    has started accumulating a consumer's domain vocabulary -- which is the thing that rots."""
    text = forecast_theme.base_qss(pal)
    for name in ("disabledRow", "#Revert", "badRegex", "#ModuleCard"):
        assert name not in text, f"{name} leaked into the base sheet"


@BOTH
def test_font_faces_reach_the_sheet(pal):
    text = forecast_theme.base_qss(pal, "TestSans", "TestDisplay", "TestMono")
    for face in ("TestSans", "TestDisplay", "TestMono"):
        assert f'"{face}"' in text


@BOTH
def test_no_pixel_font_sizes(pal):
    """Rule 4. Qt scales ``pt`` by font DPI and ``px`` only by device-pixel-ratio, so a sheet
    mixing the two does not scale together under the Windows text-size setting."""
    assert not re.findall(r"font-size:\s*[\d.]+px", forecast_theme.base_qss(pal))


@BOTH
def test_every_status_fill_is_used(pal):
    """A derived fill nobody uses is a fill nobody maintains."""
    from forecast_theme.derive import alpha

    text = forecast_theme.base_qss(pal)
    for base in (pal.accent, pal.warn, pal.danger):
        assert str(alpha(base, 0.14 if base is pal.accent else 0.12)) in text, (
            f"a fill derived from {base} is dead weight in the base sheet")
