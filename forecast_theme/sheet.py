"""The base stylesheet.

Four rules, each learned the hard way and each still load-bearing:

1. **No universal ``QWidget { background: ... }`` rule.** That is what an earlier revision had, and
   it made glass impossible: every child widget painted itself opaque, so a translucent window had
   nothing to show through. Backgrounds are declared ONLY on the surfaces that are meant to be
   surfaces. Everything else inherits nothing and stays transparent.

2. **No widget in a consuming tree may own a QGraphicsEffect.** On a window with any translucency
   Qt renders an effected widget through an offscreen cache and derives its damage region from the
   effect's bounding rect, which leaves ghosts of the previous frame behind. Depth comes from
   translucent fills and a one-pixel edge instead. Fades are done with a QVariantAnimation over a
   painted alpha, and an outer window shadow with a cached QPixmap.

3. **Never letter-space Hebrew.** ``letter-spacing`` breaks the visual join between Hebrew letters
   and reads as a rendering fault, so hierarchy here comes from size, weight and colour only.

4. **Font sizes are ``pt``, never ``px``.** Qt scales ``pt`` by the font DPI and ``px`` only by the
   device-pixel-ratio, so a sheet mixing the two does not scale together under the Windows
   text-size setting. An app appending its own rules must keep to ``pt``.

QSS is also not direction-aware -- ``border-left`` is physical and there is no logical equivalent
-- so anything whose side depends on the reading direction has to be painted in ``paintEvent``
rather than styled here.

This sheet carries stock Qt classes plus the object names in ``CONTRACT_NAMES``: the window
ground, the top bar and footer, cards and rows, buttons, pills and icon tiles. Anything specific
to one app belongs in that app's own ``qss_extra()``, appended after this one. QSS is last-wins at
equal specificity, so appending is a real override mechanism.

Every fill, hover tint and hairline below is computed from the minimal ``Palette`` core through
``derive.alpha()``/``derive.mix()``/``derive.ink_on()`` rather than read off a pre-baked named
token -- see ``palette.py`` for why the core is this small.
"""

from __future__ import annotations

from typing import Sequence

from .derive import alpha, ink_on, mix, shade
from .geometry import COMPACT, Metrics, RADIUS_CTRL, RADIUS_PANEL, RADIUS_SM
from .palette import Palette, Tone

CONTRACT_NAMES = frozenset({
    "Title", "Section", "Eyebrow", "Dim", "Faint", "Hint", "Error", "Warn", "Mono", "Status",
    "Chrome", "TopBar", "TopBarMark", "TopBarTitle", "TopBarMeta", "Footer", "FooterText",
    "FooterLink",
    "Card", "CardName", "CardDesc", "CardMeta", "Row", "RowName", "RowNote", "Rule",
    "Banner", "BannerWarn", "BannerError", "Pill", "PillText", "IconTile",
    "Primary", "Danger", "Ghost", "Chip", "Icon",
})
"""The object names this sheet styles.

A consuming app either uses one of these, or styles its own name in ``qss_extra()`` -- and a test
in each app asserts that every ``setObjectName()`` call lands in one of those two places, which is
what catches a widget left unstyled after a rename.
"""

_TONE_HOSTS = ("", "#Title", "#Section", "#Eyebrow", "#Dim", "#Faint", "#Hint", "#Error", "#Warn",
               "#Mono", "#Status", "#CardName", "#CardDesc", "#CardMeta", "#RowName", "#RowNote",
               "#TopBarTitle", "#TopBarMeta", "#PillText", "#FooterText")
"""Every label name this sheet gives a colour to.

Qt follows CSS2 specificity, so a bare ``QLabel[tone="warn"]`` loses to ``QLabel#Section`` and a
toned headline would silently keep the type scale's colour. Hence one selector per host, and the
empty string for a label with no object name at all.
"""


def tone_rules(pal: Palette, hosts: Sequence[str] = _TONE_HOSTS) -> str:
    """The ``[tone=...]`` block, generated so every host/tone pair is covered exactly once.

    Args:
        pal: The palette.
        hosts: QLabel object-name selectors that need covering, each including its leading
            ``#`` (and ``""`` for a label with no object name). An app whose own stylesheet
            gives a colour to ``QLabel#StepName`` must pass ``("#StepName", ...)`` and append
            the result to its ``qss_extra()`` -- otherwise that name out-specifies the tone
            rule and a toned label silently keeps the wrong colour.
    """
    lines = []
    for tone in Tone:
        selector = ", ".join(f'QLabel{host}[tone="{tone.value}"]' for host in hosts)
        lines.append(f"{selector} {{ color: {pal.tone(tone)}; }}")
    return "\n".join(lines)


def base_qss(pal: Palette, sans: str = "Heebo", display: str = "Rubik", mono: str = "JetBrains Mono",
        *, glass: bool = True, metrics: Metrics = COMPACT) -> str:
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
        metrics: Control sizing. ``COMPACT`` for a desktop tool, ``COMFORTABLE`` for a
            full-screen operator window.

    Returns:
        The stylesheet.

    Note:
        There are no colour literals below this line, and the test suite enforces that.
    """
    window_bg = "transparent" if glass else pal.bg

    # Panel fills: alpha over the surface colour, not a separate stored token. Light Mica tints
    # toward the wallpaper, so light mode needs a higher alpha to stay legible over a dark desktop.
    glass_fill = alpha(pal.surface, 0.86 if not pal.dark else 0.74)
    glass_hi = alpha(pal.surface, 0.94 if not pal.dark else 0.82)
    glass_low = alpha(mix(pal.surface, pal.bg, 0.5), 0.92 if not pal.dark else 0.66)

    # Hairlines: the border ink at increasing alpha. A fixed grey goes muddy in one mode and
    # invisible in the other -- ink-at-low-alpha reads on both.
    edge = alpha(pal.border, 0.16 if not pal.dark else 0.09)
    edge_hi = alpha(pal.border, 0.30 if not pal.dark else 0.20)

    # The accent as a hover/pressed shade: darker in light mode, lighter in dark mode, since the
    # accent already sits near the light end of the dark palette.
    accent_hi = shade(pal.accent, dark=pal.dark, t=0.18)
    accent_dim = mix(pal.accent, pal.surface, 0.75)
    accent_fill = alpha(pal.accent, 0.14)
    pill_ink = ink_on(pal.accent)
    on_accent_disabled = alpha(pill_ink, 0.45)

    danger_hi = shade(pal.danger, dark=pal.dark, t=0.15)
    danger_ink = ink_on(pal.danger)
    ok_fill, warn_fill, danger_fill = (alpha(c, 0.12) for c in (pal.ok, pal.warn, pal.danger))
    ok_fill_hi, warn_fill_hi, danger_fill_hi = (alpha(c, 0.22) for c in (pal.ok, pal.warn, pal.danger))

    text_faint = alpha(pal.text_dim, 0.7)
    ctrl_hover = alpha(pal.text, 0.06)
    ctrl_pressed = alpha(pal.text, 0.12)
    ctrl_disabled = alpha(pal.border, 0.35 if not pal.dark else 0.25)
    well = alpha(pal.border, 0.30)
    overlay = alpha(pal.text, 0.14)
    overlay_hi = alpha(pal.text, 0.24)

    btn_v, btn_h = metrics.btn_pad
    pill_v, pill_h = metrics.pill_pad
    chip_v, chip_h = metrics.chip_pad

    return f"""
QWidget {{
    color: {pal.text};
    font-family: "{sans}";
    font-size: {metrics.font_pt}pt;
}}

QMainWindow {{ background: {window_bg}; }}
QDialog, QMessageBox {{ background: {pal.surface}; }}

/* ---------------------------------------------------------------- window ground */
#Chrome {{ background: {pal.bg}; border-radius: {RADIUS_PANEL}px; }}

/* ---------------------------------------------------------------- top bar */
#TopBar {{ background: {glass_fill}; border: none; border-bottom: 1px solid {edge}; }}
#TopBarMark {{
    background: {glass_hi}; border: 1px solid {edge_hi}; border-radius: {RADIUS_SM}px;
}}
QLabel#TopBarTitle {{
    font-family: "{display}"; font-size: {metrics.section_pt}pt; font-weight: 700;
    color: {pal.text};
}}
QLabel#TopBarMeta {{ font-size: {metrics.small_pt}pt; color: {pal.text_dim}; }}

/* ---------------------------------------------------------------- footer */
#Footer {{ background: {glass_fill}; border: none; border-top: 1px solid {edge}; }}
QLabel#FooterText {{ font-size: {metrics.small_pt}pt; color: {pal.text_dim}; }}
QPushButton#FooterLink {{
    background: transparent; border: none; color: {text_faint};
    font-size: {metrics.small_pt}pt; padding: {btn_v}px {btn_h}px;
}}
QPushButton#FooterLink:hover {{ color: {pal.text}; }}
QPushButton#FooterLink:focus {{ color: {pal.accent_ink}; }}

/* ---------------------------------------------------------------- type scale */
QLabel#Title {{
    font-family: "{display}"; font-size: {metrics.title_pt}pt; font-weight: 600; color: {pal.text};
}}
QLabel#Section {{
    font-family: "{display}"; font-size: {metrics.section_pt}pt; font-weight: 500;
    color: {pal.text};
}}
QLabel#Eyebrow {{
    font-family: "{display}"; font-size: {metrics.small_pt}pt; font-weight: 500;
    color: {pal.text_dim};
}}
QLabel#Dim {{ color: {pal.text_dim}; }}
QLabel#Status {{ color: {pal.text_dim}; }}
QLabel#Faint {{ color: {text_faint}; font-size: {metrics.small_pt}pt; }}
QLabel#Hint {{ color: {text_faint}; font-size: {metrics.small_pt}pt; }}
QLabel#Error {{ color: {pal.danger}; font-size: {metrics.small_pt}pt; }}
QLabel#Warn {{ color: {pal.warn}; font-size: {metrics.small_pt}pt; }}
QLabel#Mono {{
    font-family: "{mono}"; font-size: {metrics.small_pt}pt; color: {pal.text_dim};
}}

{tone_rules(pal)}

/* ---------------------------------------------------------------- cards */
#Card {{
    background: {glass_fill};
    border: 1px solid {edge};
    border-top: 1px solid {edge_hi};
    border-radius: {RADIUS_PANEL}px;
}}
#Card[hovered="true"] {{ background: {glass_hi}; border-color: {pal.accent_ink}; }}
#Card[focused="true"] {{ border-color: {pal.accent_ink}; }}
#Card[broken="true"] {{ border-color: {pal.danger}; }}
#Card[state="running"] {{
    background: {accent_fill}; border: 1px solid {pal.accent_ink};
}}
#Card[state="done"] {{ background: {ok_fill}; border: 1px solid {pal.ok}; }}
#Card[state="warn"] {{ background: {warn_fill}; border: 1px solid {pal.warn}; }}
#Card[state="failed"] {{ background: {danger_fill}; border: 1px solid {pal.danger}; }}

QLabel#CardName {{
    font-family: "{display}"; font-size: {metrics.section_pt}pt; font-weight: 700;
    color: {pal.text};
}}
QLabel#CardDesc {{ font-size: {metrics.small_pt}pt; color: {pal.text_dim}; }}
QLabel#CardMeta {{
    font-family: "{mono}"; font-size: {metrics.small_pt}pt; color: {text_faint};
}}
#Card[dim="true"] QLabel#CardName {{ color: {pal.text_dim}; }}

/* ---------------------------------------------------------------- rows */
#Row {{
    background: {glass_fill}; border: 1px solid {edge}; border-radius: {RADIUS_CTRL}px;
}}
#Row[hovered="true"] {{ border-color: {pal.accent_ink}; }}
#Row[selected="true"] {{ border-color: {pal.accent_ink}; background: {accent_fill}; }}
QLabel#RowName {{ font-weight: 600; color: {pal.text}; }}
QLabel#RowNote {{ font-size: {metrics.small_pt}pt; color: {pal.text_dim}; }}

#Rule {{
    background: {pal.accent}; border: none; max-height: 1px; min-height: 1px;
}}

/* ---------------------------------------------------------------- pills and tiles */
#Pill {{
    background: {glass_hi}; border: 1px solid {edge}; border-radius: {RADIUS_SM}px;
}}
#Pill[kind="warn"] {{ background: {warn_fill}; border-color: {pal.warn}; }}
#Pill[kind="error"] {{ background: {danger_fill}; border-color: {pal.danger}; }}
#Pill[kind="ok"] {{ background: {ok_fill}; border-color: {pal.ok}; }}
QLabel#PillText {{ font-size: {metrics.small_pt}pt; color: {pal.text_dim}; }}

#IconTile {{
    background: {accent_fill}; border: 1px solid {pal.accent_ink};
    border-radius: {RADIUS_SM}px;
}}
#IconTile[kind="warn"] {{ background: {warn_fill}; border-color: {pal.warn}; }}
#IconTile[kind="error"] {{ background: {danger_fill}; border-color: {pal.danger}; }}
#IconTile[kind="dim"] {{ background: transparent; border-color: {edge}; }}
#IconTile[kind="plain"] {{ background: transparent; border-color: transparent; }}

/* ---------------------------------------------------------------- buttons */
QPushButton {{
    background: {glass_hi};
    border: 1px solid {edge};
    border-radius: {RADIUS_CTRL}px;
    padding: {btn_v}px {btn_h}px;
    color: {pal.text};
}}
QPushButton:hover {{ background: {ctrl_hover}; border-color: {edge_hi}; }}
QPushButton:pressed {{ background: {ctrl_pressed}; }}
QPushButton:disabled {{
    color: {text_faint}; background: {glass_low}; border-color: {edge};
}}

QPushButton[accent="warn"] {{
    background: {warn_fill}; border-color: {pal.warn}; color: {pal.warn}; font-weight: 600;
}}
QPushButton[accent="warn"]:hover {{ background: {warn_fill_hi}; }}
QPushButton[accent="danger"] {{
    background: {danger_fill}; border-color: {pal.danger}; color: {pal.danger};
    font-weight: 600;
}}
QPushButton[accent="danger"]:hover {{ background: {danger_fill_hi}; }}
QPushButton[accent="ok"] {{
    background: {ok_fill}; border-color: {pal.ok}; color: {pal.ok}; font-weight: 600;
}}
QPushButton[accent="ok"]:hover {{ background: {ok_fill_hi}; }}

QPushButton#Primary {{
    background: {pal.accent}; border: 1px solid {pal.accent};
    border-radius: {metrics.pill_radius}px;
    color: {pill_ink}; font-weight: 600; padding: {pill_v}px {pill_h}px;
}}
QPushButton#Primary:hover {{ background: {accent_hi}; border-color: {accent_hi}; }}
QPushButton#Primary:disabled {{
    background: {accent_dim}; border-color: {accent_dim}; color: {on_accent_disabled};
}}
QPushButton#Danger {{
    background: {pal.danger}; border-color: {pal.danger}; color: {danger_ink};
    font-weight: 600; border-radius: {metrics.pill_radius}px; padding: {pill_v}px {pill_h}px;
}}
QPushButton#Danger:hover {{ background: {danger_hi}; border-color: {danger_hi}; }}
QPushButton#Ghost {{
    background: transparent; border: none; color: {pal.text_dim};
    padding: {btn_v}px {btn_h}px;
}}
QPushButton#Ghost:hover {{ color: {pal.text}; background: {glass_hi}; }}

QPushButton#Icon {{
    background: transparent; border: none; color: {pal.text_dim}; padding: {btn_v}px;
}}
QPushButton#Icon:hover {{ background: {glass_hi}; color: {pal.text}; }}
QPushButton#Icon:pressed {{ background: {accent_fill}; }}
QPushButton#Icon:focus {{ border: 1px solid {pal.accent_ink}; }}
QPushButton#Icon[accent="danger"]:hover {{
    background: {danger_fill_hi}; color: {pal.danger};
}}

QPushButton#Chip {{
    background: transparent; border: 1px solid {edge};
    border-radius: {metrics.chip_radius}px; padding: {chip_v}px {chip_h}px;
    color: {pal.text_dim}; font-size: {metrics.small_pt}pt;
}}
QPushButton#Chip:hover, QPushButton#Chip[on="false"]:hover {{
    color: {pal.text}; border-color: {edge_hi}; background: {accent_fill};
}}
QPushButton#Chip:checked, QPushButton#Chip[on="true"] {{
    background: {pal.accent}; color: {pill_ink}; border-color: {pal.accent};
    font-weight: 600;
}}
QPushButton#Chip:checked:hover, QPushButton#Chip[on="true"]:hover {{
    background: {accent_hi}; border-color: {accent_hi};
}}

/* ---------------------------------------------------------------- inputs */
QLineEdit, QComboBox {{
    background: {glass_low};
    border: 1px solid {edge};
    border-radius: {RADIUS_CTRL}px;
    padding: {btn_v}px 10px;
    color: {pal.text};
    selection-background-color: {accent_dim};
    selection-color: {pal.text};
}}
QLineEdit:hover, QComboBox:hover {{ border-color: {edge_hi}; }}
QLineEdit:focus, QComboBox:focus {{ border-color: {pal.accent_ink}; }}
QLineEdit[invalid="true"] {{ border-color: {pal.danger}; }}
QLineEdit[warn="true"] {{ border-color: {pal.warn}; }}
QLineEdit:disabled {{ color: {text_faint}; background: {ctrl_disabled}; }}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background: {pal.surface}; border: 1px solid {edge_hi}; border-radius: {RADIUS_CTRL}px;
    selection-background-color: {accent_dim}; selection-color: {pal.text}; padding: 4px;
}}

ToggleSwitch:focus {{ border: none; outline: none; }}

/* ---------------------------------------------------------------- scrolling */
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{
    background: {overlay}; border-radius: 5px; min-height: 34px;
}}
QScrollBar::handle:vertical:hover {{ background: {overlay_hi}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 0; }}
QScrollBar::handle:horizontal {{
    background: {overlay}; border-radius: 5px; min-width: 34px;
}}
QScrollBar::handle:horizontal:hover {{ background: {overlay_hi}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* ---------------------------------------------------------------- progress */
QProgressBar {{
    background: {well}; border: none; border-radius: 3px; height: 6px;
    text-align: center;
}}
QProgressBar::chunk {{ background: {pal.accent}; border-radius: 3px; }}

/* ---------------------------------------------------------------- lists */
QTreeView, QListWidget, QListView {{
    background: {glass_low}; border: 1px solid {edge}; border-radius: {RADIUS_CTRL}px;
    color: {pal.text};
}}
QTreeView {{ font-family: "{mono}"; font-size: {metrics.small_pt}pt; }}
QTreeView::item {{ padding: 1px 4px; }}
QListWidget::item, QListView::item {{ padding: 6px 8px; }}
QTreeView::item:selected, QListWidget::item:selected, QListView::item:selected {{
    background: {accent_dim}; color: {pal.text};
}}
QListWidget::item:hover, QListView::item:hover {{ background: {ctrl_hover}; }}
QHeaderView::section {{
    background: transparent; border: none; border-bottom: 1px solid {edge}; padding: 4px;
}}

/* ---------------------------------------------------------------- program output */
QTextEdit#Log, QPlainTextEdit#Log {{
    background: {glass_low}; border: 1px solid {edge}; border-radius: {RADIUS_CTRL}px;
    font-family: "{mono}"; font-size: {metrics.small_pt}pt; color: {pal.text_dim};
}}

QToolTip {{
    background: {pal.surface}; color: {pal.text}; border: 1px solid {edge_hi};
    border-radius: {RADIUS_CTRL}px; padding: 7px 9px;
}}

/* ---------------------------------------------------------------- banners */
#Banner {{
    background: {glass_hi}; border: 1px solid {edge_hi}; border-radius: {RADIUS_CTRL}px;
}}
#BannerWarn {{
    background: {warn_fill}; border: 1px solid {pal.warn};
    border-radius: {RADIUS_CTRL}px;
}}
#BannerError {{
    background: {danger_fill}; border: 1px solid {pal.danger};
    border-radius: {RADIUS_CTRL}px;
}}
QSplitter::handle {{ background: transparent; }}
"""
