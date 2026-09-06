"""The base stylesheet.

Four rules, each learned the hard way and each still load-bearing:

1. **No universal ``QWidget { background: ... }`` rule.** That is what an earlier revision had, and
   it made glass impossible: every child widget painted itself opaque, so a translucent window had
   nothing to show through. Backgrounds are declared ONLY on the surfaces that are meant to be
   surfaces. Everything else inherits nothing and stays transparent.

2. **No widget in a consuming tree may own a QGraphicsEffect.** On a window with any translucency
   Qt renders an effected widget through an offscreen cache and derives its damage region from the
   effect's bounding rect, which leaves ghosts of the previous frame behind. Depth comes from
   translucent fills and a one-pixel edge -- which is the Windows 11 idiom anyway. Fades are done
   with a QVariantAnimation over a painted alpha, and an outer window shadow with a cached QPixmap.

3. **Never letter-space Hebrew.** ``letter-spacing`` breaks the visual join between Hebrew letters
   and reads as a rendering fault, so hierarchy here comes from size, weight and colour only.

4. **Font sizes are ``pt``, never ``px``.** Qt scales ``pt`` by the font DPI and ``px`` only by the
   device-pixel-ratio, so a sheet mixing the two does not scale together under the Windows
   text-size setting. An app appending its own rules must keep to ``pt``.

QSS is also not direction-aware -- ``border-left`` is physical and there is no logical equivalent
-- so anything whose side depends on the reading direction has to be painted in ``paintEvent``
rather than styled here.

This sheet carries stock Qt classes plus the object names in ``CONTRACT_NAMES``. Anything specific
to one app -- its own widgets, its own dynamic properties -- belongs in that app's own
``qss_extra()``, appended after this one. QSS is last-wins at equal specificity, so appending is a
real override mechanism.
"""

from __future__ import annotations

from typing import Sequence

from .geometry import RADIUS_CTRL, RADIUS_PANEL, RADIUS_PILL, RADIUS_PILL_LG
from .palette import Palette, Tone

# The object names this sheet styles. A consuming app either uses one of these, or styles its own
# name in qss_extra() -- and a test in each app asserts that every setObjectName() call lands in
# one of those two places, which is what catches a widget left unstyled after a rename.
CONTRACT_NAMES = frozenset({
    # type scale
    "Title", "Section", "Eyebrow", "Dim", "Faint", "Error", "Warn", "Mono",
    # surfaces
    "Card", "Rule", "Banner", "BannerWarn", "BannerError",
    # buttons
    "Primary", "Danger", "Ghost", "Chip",
})

# Qt follows CSS2 specificity: a bare ``QLabel[tone="ok"]`` loses to ``QLabel#Section``, so a
# toned headline would silently keep the type scale's colour. Hence one selector per host, and the
# empty string for a label with no object name at all.
_TONE_HOSTS = ("", "#Title", "#Section", "#Eyebrow", "#Dim", "#Faint", "#Error", "#Warn",
               "#Mono")


def tone_rules(pal: Palette, hosts: Sequence[str] = _TONE_HOSTS) -> str:
    """The ``[tone=...]`` block, generated so every host/tone pair is covered exactly once.

    Args:
        pal: The palette.
        hosts: QLabel object-name selectors that need covering, each including its leading
            ``#`` (and ``""`` for a label with no object name). An app whose own stylesheet
            gives a colour to ``QLabel#CardName`` must pass ``("#CardName", ...)`` and append
            the result to its ``qss_extra()`` -- otherwise that name out-specifies the tone
            rule and a toned label silently keeps the wrong colour.
    """
    lines = []
    for tone in Tone:
        selector = ", ".join(f'QLabel{host}[tone="{tone.value}"]' for host in hosts)
        lines.append(f"{selector} {{ color: {pal.tone(tone)}; }}")
    return "\n".join(lines)


def base_qss(pal: Palette, sans: str = "Heebo", display: str = "Rubik", mono: str = "JetBrains Mono",
        *, glass: bool = True) -> str:
    """The application stylesheet.

    Args:
        pal: The palette. Required and positional rather than defaulting to ``active()``, so the
            build smoke test can compile every palette against every backdrop without mutating
            global state.
        sans: Body face. Everything the operator reads is set in this.
        display: Face for the title and section headings, used with restraint.
        mono: Face for program output, paths and numbers -- always LTR content.
        glass: True when the native backdrop was accepted, so the window can be transparent.
            False paints an opaque base instead, which is the path a machine with transparency
            effects turned off takes. It has to look deliberate rather than broken.

    Returns:
        The stylesheet.

    Note:
        There are no colour literals below this line, and ``tests/test_theme.py`` enforces that.
        Every one that used to be here -- the scrollbar handle, the toggle track, the progress
        well, the primary button's ink -- was a dark-mode assumption that would have shipped a
        light mode with invisible controls.
    """
    window_bg = "transparent" if glass else pal.void

    return f"""
/* Colour and type only -- deliberately NO background here, see rule 1 in the module docstring. */
QWidget {{
    color: {pal.text};
    font-family: "{sans}";
    font-size: 10pt;
}}

/* Split, because only MainWindow sets WA_TranslucentBackground. A QDialog -- the cancel, reset and
   close-during-run confirmations, and the environment page -- has no backdrop to show through, so
   a transparent fill leaves its text on whatever the desktop happens to be painting. That survived
   by accident while the text was near-white; near-black text in light mode would not. */
QMainWindow {{ background: {window_bg}; }}
QDialog, QMessageBox {{ background: {pal.depth}; }}

/* ---------------------------------------------------------------- type scale */
QLabel#Title {{
    font-family: "{display}"; font-size: 19pt; font-weight: 600; color: {pal.text};
}}
QLabel#Section {{
    font-family: "{display}"; font-size: 12pt; font-weight: 500; color: {pal.text};
}}
QLabel#Eyebrow {{
    font-family: "{display}"; font-size: 9pt; font-weight: 500; color: {pal.text_dim};
}}
QLabel#Dim {{ color: {pal.text_dim}; }}
QLabel#Faint {{ color: {pal.text_faint}; font-size: 9pt; }}
QLabel#Error {{ color: {pal.danger}; font-size: 9pt; }}
QLabel#Warn {{ color: {pal.warn}; font-size: 9pt; }}
QLabel#Mono {{ font-family: "{mono}"; font-size: 9pt; color: {pal.text_dim}; }}

/* Severity and outcome colours as a property the stylesheet reads, rather than an inline sheet on
   the widget. An inline sheet outranks this one permanently, so a label coloured that way could
   never be re-themed -- and the two that mattered were only ever set inside show_verdict(), which
   may never be called again. Set with ui.styling.set_tone(). */
{tone_rules(pal)}

/* ---------------------------------------------------------------- surfaces */
QFrame#Card {{
    background: {pal.glass};
    border: 1px solid {pal.edge};
    border-top: 1px solid {pal.edge_top};
    border-radius: {RADIUS_PANEL}px;
}}

/* The slide's section separator: a thin solid apricot rule. Decorative, so it is the only place
   the accent is allowed at full strength as a line. */
QFrame#Rule {{
    background: {pal.rule}; border: none; max-height: 1px; min-height: 1px;
}}

/* ---------------------------------------------------------------- buttons */
QPushButton {{
    background: {pal.glass_hi};
    border: 1px solid {pal.edge};
    border-radius: {RADIUS_CTRL}px;
    padding: 6px 14px;
    color: {pal.text};
}}
QPushButton:hover {{ background: {pal.ctrl_hover}; border-color: {pal.edge_hi}; }}
QPushButton:pressed {{ background: {pal.ctrl_pressed}; }}
QPushButton:disabled {{
    color: {pal.text_faint}; background: {pal.glass_low}; border-color: {pal.edge};
}}

/* The slide's stadium pill, in the slide's apricot, with a deep warm ink instead of the slide's
   white -- white on this fill is 2.06:1, and this is the primary action. */
QPushButton#Primary {{
    background: {pal.accent}; border: 1px solid {pal.accent}; border-radius: {RADIUS_PILL_LG}px;
    color: {pal.pill_ink}; font-weight: 600; padding: 9px 26px;
}}
QPushButton#Primary:hover {{ background: {pal.accent_hi}; border-color: {pal.accent_hi}; }}
QPushButton#Primary:disabled {{
    background: {pal.accent_dim}; border-color: {pal.accent_dim}; color: {pal.on_accent_disabled};
}}
QPushButton#Danger {{
    background: {pal.danger}; border-color: {pal.danger}; color: {pal.danger_ink};
    font-weight: 600; border-radius: {RADIUS_PILL_LG}px; padding: 9px 26px;
}}
QPushButton#Danger:hover {{ background: {pal.danger_hi}; border-color: {pal.danger_hi}; }}
QPushButton#Ghost {{
    background: transparent; border: none; color: {pal.text_dim}; padding: 4px 8px;
}}
QPushButton#Ghost:hover {{ color: {pal.text}; background: {pal.glass_hi}; }}

/* Checked chips are a filled pill rather than tinted outline text, because the accent is not a
   usable ink in light mode -- and because a filled pill is the slide's own idiom for "this one". */
QPushButton#Chip {{
    background: transparent; border: 1px solid {pal.edge};
    border-radius: {RADIUS_PILL}px; padding: 4px 13px; color: {pal.text_dim}; font-size: 9pt;
}}
QPushButton#Chip:hover {{
    color: {pal.text}; border-color: {pal.edge_hi}; background: {pal.accent_fill};
}}
QPushButton#Chip:checked {{
    background: {pal.accent}; color: {pal.pill_ink}; border-color: {pal.accent};
    font-weight: 600;
}}
QPushButton#Chip:checked:hover {{ background: {pal.accent_hi}; border-color: {pal.accent_hi}; }}

/* ---------------------------------------------------------------- inputs */
QLineEdit, QComboBox {{
    background: {pal.glass_low};
    border: 1px solid {pal.edge};
    border-radius: {RADIUS_CTRL}px;
    padding: 6px 10px;
    color: {pal.text};
    selection-background-color: {pal.accent_dim};
    selection-color: {pal.text};
}}
QLineEdit:hover, QComboBox:hover {{ border-color: {pal.edge_hi}; }}
/* ACCENT_LINE, not ACCENT: this is the keyboard focus indicator, and a 1px apricot border on the
   light ground is 1.56:1 -- invisible to exactly the operator who depends on it. */
QLineEdit:focus, QComboBox:focus {{ border-color: {pal.accent_line}; }}
QLineEdit[invalid="true"] {{ border-color: {pal.danger}; }}
QLineEdit[warn="true"] {{ border-color: {pal.warn}; }}
QLineEdit:disabled {{ color: {pal.text_faint}; background: {pal.ctrl_disabled}; }}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background: {pal.depth}; border: 1px solid {pal.edge_hi}; border-radius: {RADIUS_CTRL}px;
    selection-background-color: {pal.accent_dim}; selection-color: {pal.text}; padding: 4px;
}}

/* The bool control is ui.switch.ToggleSwitch, painted from the track/knob tokens -- neither a knob
   that moves nor a ring around it can be expressed in QSS, so the focus indicator is painted too.
   This rule only stops the style from adding a rectangular one around the capsule. */
ToggleSwitch:focus {{ border: none; outline: none; }}

/* ---------------------------------------------------------------- scrolling */
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{
    background: {pal.overlay}; border-radius: 5px; min-height: 34px;
}}
QScrollBar::handle:vertical:hover {{ background: {pal.overlay_hi}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 0; }}
QScrollBar::handle:horizontal {{
    background: {pal.overlay}; border-radius: 5px; min-width: 34px;
}}
QScrollBar::handle:horizontal:hover {{ background: {pal.overlay_hi}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* ---------------------------------------------------------------- progress */
QProgressBar {{
    background: {pal.well}; border: none; border-radius: 3px; height: 6px;
    text-align: center;
}}
QProgressBar::chunk {{ background: {pal.accent}; border-radius: 3px; }}

/* ---------------------------------------------------------------- the log */
QTreeView {{
    background: {pal.glass_low}; border: 1px solid {pal.edge}; border-radius: {RADIUS_CTRL}px;
    font-family: "{mono}"; font-size: 9pt;
}}
QTreeView::item {{ padding: 1px 4px; }}
QTreeView::item:selected {{ background: {pal.accent_dim}; color: {pal.text}; }}
QHeaderView::section {{
    background: transparent; border: none; border-bottom: 1px solid {pal.edge}; padding: 4px;
}}

QToolTip {{
    background: {pal.depth}; color: {pal.text}; border: 1px solid {pal.edge_hi};
    border-radius: {RADIUS_CTRL}px; padding: 7px 9px;
}}

/* ---------------------------------------------------------------- banners */
QFrame#Banner {{
    background: {pal.glass_hi}; border: 1px solid {pal.edge_hi}; border-radius: {RADIUS_CTRL}px;
}}
QFrame#BannerWarn {{
    background: {pal.warn_fill}; border: 1px solid {pal.warn};
    border-radius: {RADIUS_CTRL}px;
}}
QFrame#BannerError {{
    background: {pal.danger_fill}; border: 1px solid {pal.danger};
    border-radius: {RADIUS_CTRL}px;
}}
QSplitter::handle {{ background: transparent; }}
"""
