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

This sheet carries stock Qt classes plus the object names in ``CONTRACT_NAMES``: the window
ground, the top bar and footer, cards and rows, buttons, pills and icon tiles. Anything specific
to one app belongs in that app's own ``qss_extra()``, appended after this one. QSS is last-wins at
equal specificity, so appending is a real override mechanism.

Two widgets that look alike across apps must therefore wear the same name here rather than being
restyled locally: a card is ``#Card`` in all of them, not ``#Step`` in one and ``#ModuleCard`` in
another. Density is the one axis apps legitimately differ on, and it travels as a ``Metrics``
preset rather than as an app-local override of ``QPushButton``.

Surfaces are styled by object name alone -- ``#Card``, not ``QFrame#Card``. A card is not always a
QFrame: paper-gui's module card is a plain QWidget subclass that paints its own accent rule, and a
class-qualified selector silently skipped it, leaving the card with no fill and no border at all.
"""

from __future__ import annotations

from typing import Sequence

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
            full-screen operator window. An app that wants larger controls picks a preset here
            instead of overriding ``QPushButton`` in its own sheet, which is what made buttons a
            different shape in each app.

    Returns:
        The stylesheet.

    Note:
        There are no colour literals below this line, and the test suite enforces that. Every one
        that used to be here -- the scrollbar handle, the toggle track, the progress well, the
        primary button's ink -- was a dark-mode assumption that would have shipped a light mode
        with invisible controls.

        A severity button never goes to a solid fill on hover. ``warn`` and ``ok`` invert
        lightness between the modes -- amber-800 on the light ground, yellow-400 on the dark one
        -- so no single ink stays readable on top of them: light ``pill_ink`` on solid ``warn``
        measures 2.36:1. Hover deepens the tint instead and keeps the semantic ink, and the
        ``*_fill_hi`` alphas are the highest that still clear 4.5:1 for their own ink.
    """
    window_bg = "transparent" if glass else pal.void
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
QDialog, QMessageBox {{ background: {pal.depth}; }}

/* ---------------------------------------------------------------- window ground */
#Chrome {{ background: {pal.void}; border-radius: {RADIUS_PANEL}px; }}

/* ---------------------------------------------------------------- top bar */
#TopBar {{ background: {pal.glass}; border: none; border-bottom: 1px solid {pal.edge}; }}
#TopBarMark {{
    background: {pal.glass_hi}; border: 1px solid {pal.edge_hi}; border-radius: {RADIUS_SM}px;
}}
QLabel#TopBarTitle {{
    font-family: "{display}"; font-size: {metrics.section_pt}pt; font-weight: 700;
    color: {pal.text};
}}
QLabel#TopBarMeta {{ font-size: {metrics.small_pt}pt; color: {pal.text_dim}; }}

/* ---------------------------------------------------------------- footer */
#Footer {{ background: {pal.glass}; border: none; border-top: 1px solid {pal.edge}; }}
QLabel#FooterText {{ font-size: {metrics.small_pt}pt; color: {pal.text_dim}; }}
QPushButton#FooterLink {{
    background: transparent; border: none; color: {pal.text_faint};
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
QLabel#Faint {{ color: {pal.text_faint}; font-size: {metrics.small_pt}pt; }}
QLabel#Hint {{ color: {pal.text_faint}; font-size: {metrics.small_pt}pt; }}
QLabel#Error {{ color: {pal.danger}; font-size: {metrics.small_pt}pt; }}
QLabel#Warn {{ color: {pal.warn}; font-size: {metrics.small_pt}pt; }}
QLabel#Mono {{
    font-family: "{mono}"; font-size: {metrics.small_pt}pt; color: {pal.text_dim};
}}

{tone_rules(pal)}

/* ---------------------------------------------------------------- cards */
#Card {{
    background: {pal.glass};
    border: 1px solid {pal.edge};
    border-top: 1px solid {pal.edge_top};
    border-radius: {RADIUS_PANEL}px;
}}
#Card[hovered="true"] {{ background: {pal.glass_hi}; border-color: {pal.accent_line}; }}
#Card[focused="true"] {{ border-color: {pal.accent_line}; }}
#Card[broken="true"] {{ border-color: {pal.danger}; }}
#Card[state="running"] {{
    background: {pal.accent_fill}; border: 1px solid {pal.accent_line};
}}
#Card[state="done"] {{ background: {pal.ok_fill}; border: 1px solid {pal.ok}; }}
#Card[state="warn"] {{ background: {pal.warn_fill}; border: 1px solid {pal.warn}; }}
#Card[state="failed"] {{ background: {pal.danger_fill}; border: 1px solid {pal.danger}; }}

QLabel#CardName {{
    font-family: "{display}"; font-size: {metrics.section_pt}pt; font-weight: 700;
    color: {pal.text};
}}
QLabel#CardDesc {{ font-size: {metrics.small_pt}pt; color: {pal.text_dim}; }}
QLabel#CardMeta {{
    font-family: "{mono}"; font-size: {metrics.small_pt}pt; color: {pal.text_faint};
}}
#Card[dim="true"] QLabel#CardName {{ color: {pal.text_dim}; }}

/* ---------------------------------------------------------------- rows */
#Row {{
    background: {pal.glass}; border: 1px solid {pal.edge}; border-radius: {RADIUS_CTRL}px;
}}
#Row[hovered="true"] {{ border-color: {pal.accent_line}; }}
#Row[selected="true"] {{ border-color: {pal.accent_line}; background: {pal.accent_fill}; }}
QLabel#RowName {{ font-weight: 600; color: {pal.text}; }}
QLabel#RowNote {{ font-size: {metrics.small_pt}pt; color: {pal.text_dim}; }}

#Rule {{
    background: {pal.rule}; border: none; max-height: 1px; min-height: 1px;
}}

/* ---------------------------------------------------------------- pills and tiles */
#Pill {{
    background: {pal.glass_hi}; border: 1px solid {pal.edge}; border-radius: {RADIUS_SM}px;
}}
#Pill[kind="warn"] {{ background: {pal.warn_fill}; border-color: {pal.warn}; }}
#Pill[kind="error"] {{ background: {pal.danger_fill}; border-color: {pal.danger}; }}
#Pill[kind="ok"] {{ background: {pal.ok_fill}; border-color: {pal.ok}; }}
QLabel#PillText {{ font-size: {metrics.small_pt}pt; color: {pal.text_dim}; }}

#IconTile {{
    background: {pal.accent_fill}; border: 1px solid {pal.accent_line};
    border-radius: {RADIUS_SM}px;
}}
#IconTile[kind="warn"] {{ background: {pal.warn_fill}; border-color: {pal.warn}; }}
#IconTile[kind="error"] {{ background: {pal.danger_fill}; border-color: {pal.danger}; }}
#IconTile[kind="dim"] {{ background: transparent; border-color: {pal.edge}; }}
#IconTile[kind="plain"] {{ background: transparent; border-color: transparent; }}

/* ---------------------------------------------------------------- buttons */
QPushButton {{
    background: {pal.glass_hi};
    border: 1px solid {pal.edge};
    border-radius: {RADIUS_CTRL}px;
    padding: {btn_v}px {btn_h}px;
    color: {pal.text};
}}
QPushButton:hover {{ background: {pal.ctrl_hover}; border-color: {pal.edge_hi}; }}
QPushButton:pressed {{ background: {pal.ctrl_pressed}; }}
QPushButton:disabled {{
    color: {pal.text_faint}; background: {pal.glass_low}; border-color: {pal.edge};
}}

QPushButton[accent="warn"] {{
    background: {pal.warn_fill}; border-color: {pal.warn}; color: {pal.warn}; font-weight: 600;
}}
QPushButton[accent="warn"]:hover {{ background: {pal.warn_fill_hi}; }}
QPushButton[accent="danger"] {{
    background: {pal.danger_fill}; border-color: {pal.danger}; color: {pal.danger};
    font-weight: 600;
}}
QPushButton[accent="danger"]:hover {{ background: {pal.danger_fill_hi}; }}
QPushButton[accent="ok"] {{
    background: {pal.ok_fill}; border-color: {pal.ok}; color: {pal.ok}; font-weight: 600;
}}
QPushButton[accent="ok"]:hover {{ background: {pal.ok_fill_hi}; }}

QPushButton#Primary {{
    background: {pal.accent}; border: 1px solid {pal.accent};
    border-radius: {metrics.pill_radius}px;
    color: {pal.pill_ink}; font-weight: 600; padding: {pill_v}px {pill_h}px;
}}
QPushButton#Primary:hover {{ background: {pal.accent_hi}; border-color: {pal.accent_hi}; }}
QPushButton#Primary:disabled {{
    background: {pal.accent_dim}; border-color: {pal.accent_dim}; color: {pal.on_accent_disabled};
}}
QPushButton#Danger {{
    background: {pal.danger}; border-color: {pal.danger}; color: {pal.danger_ink};
    font-weight: 600; border-radius: {metrics.pill_radius}px; padding: {pill_v}px {pill_h}px;
}}
QPushButton#Danger:hover {{ background: {pal.danger_hi}; border-color: {pal.danger_hi}; }}
QPushButton#Ghost {{
    background: transparent; border: none; color: {pal.text_dim};
    padding: {btn_v}px {btn_h}px;
}}
QPushButton#Ghost:hover {{ color: {pal.text}; background: {pal.glass_hi}; }}

QPushButton#Icon {{
    background: transparent; border: none; color: {pal.text_dim}; padding: {btn_v}px;
}}
QPushButton#Icon:hover {{ background: {pal.glass_hi}; color: {pal.text}; }}
QPushButton#Icon:pressed {{ background: {pal.accent_fill}; }}
QPushButton#Icon:focus {{ border: 1px solid {pal.accent_line}; }}
QPushButton#Icon[accent="danger"]:hover {{
    background: {pal.danger_fill_hi}; color: {pal.danger};
}}

QPushButton#Chip {{
    background: transparent; border: 1px solid {pal.edge};
    border-radius: {metrics.chip_radius}px; padding: {chip_v}px {chip_h}px;
    color: {pal.text_dim}; font-size: {metrics.small_pt}pt;
}}
QPushButton#Chip:hover, QPushButton#Chip[on="false"]:hover {{
    color: {pal.text}; border-color: {pal.edge_hi}; background: {pal.accent_fill};
}}
QPushButton#Chip:checked, QPushButton#Chip[on="true"] {{
    background: {pal.accent}; color: {pal.pill_ink}; border-color: {pal.accent};
    font-weight: 600;
}}
QPushButton#Chip:checked:hover, QPushButton#Chip[on="true"]:hover {{
    background: {pal.accent_hi}; border-color: {pal.accent_hi};
}}

/* ---------------------------------------------------------------- inputs */
QLineEdit, QComboBox {{
    background: {pal.glass_low};
    border: 1px solid {pal.edge};
    border-radius: {RADIUS_CTRL}px;
    padding: {btn_v}px 10px;
    color: {pal.text};
    selection-background-color: {pal.accent_dim};
    selection-color: {pal.text};
}}
QLineEdit:hover, QComboBox:hover {{ border-color: {pal.edge_hi}; }}
QLineEdit:focus, QComboBox:focus {{ border-color: {pal.accent_line}; }}
QLineEdit[invalid="true"] {{ border-color: {pal.danger}; }}
QLineEdit[warn="true"] {{ border-color: {pal.warn}; }}
QLineEdit:disabled {{ color: {pal.text_faint}; background: {pal.ctrl_disabled}; }}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background: {pal.depth}; border: 1px solid {pal.edge_hi}; border-radius: {RADIUS_CTRL}px;
    selection-background-color: {pal.accent_dim}; selection-color: {pal.text}; padding: 4px;
}}

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

/* ---------------------------------------------------------------- lists */
QTreeView, QListWidget, QListView {{
    background: {pal.glass_low}; border: 1px solid {pal.edge}; border-radius: {RADIUS_CTRL}px;
    color: {pal.text};
}}
QTreeView {{ font-family: "{mono}"; font-size: {metrics.small_pt}pt; }}
QTreeView::item {{ padding: 1px 4px; }}
QListWidget::item, QListView::item {{ padding: 6px 8px; }}
QTreeView::item:selected, QListWidget::item:selected, QListView::item:selected {{
    background: {pal.accent_dim}; color: {pal.text};
}}
QListWidget::item:hover, QListView::item:hover {{ background: {pal.ctrl_hover}; }}
QHeaderView::section {{
    background: transparent; border: none; border-bottom: 1px solid {pal.edge}; padding: 4px;
}}

/* ---------------------------------------------------------------- program output */
QTextEdit#Log, QPlainTextEdit#Log {{
    background: {pal.glass_low}; border: 1px solid {pal.edge}; border-radius: {RADIUS_CTRL}px;
    font-family: "{mono}"; font-size: {metrics.small_pt}pt; color: {pal.text_dim};
}}

QToolTip {{
    background: {pal.depth}; color: {pal.text}; border: 1px solid {pal.edge_hi};
    border-radius: {RADIUS_CTRL}px; padding: 7px 9px;
}}

/* ---------------------------------------------------------------- banners */
#Banner {{
    background: {pal.glass_hi}; border: 1px solid {pal.edge_hi}; border-radius: {RADIUS_CTRL}px;
}}
#BannerWarn {{
    background: {pal.warn_fill}; border: 1px solid {pal.warn};
    border-radius: {RADIUS_CTRL}px;
}}
#BannerError {{
    background: {pal.danger_fill}; border: 1px solid {pal.danger};
    border-radius: {RADIUS_CTRL}px;
}}
QSplitter::handle {{ background: transparent; }}
"""
