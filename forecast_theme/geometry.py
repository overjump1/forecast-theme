"""Geometry: the measurements that are identity rather than appearance.

Nothing here is per-mode. A radius is not an appearance -- a card is the same shape in
light and dark -- so these are plain module constants rather than fields on ``Palette``.

Kept out of ``palette.py`` so a palette stays purely about colour, and out of ``sheet.py``
so painting code can import a radius without pulling in the stylesheet.
"""

from __future__ import annotations

from dataclasses import dataclass

RADIUS_PANEL = 14
RADIUS_CTRL = 8
RADIUS_SM = 6
RADIUS_PILL_LG = 20
RADIUS_PILL = 14

S1, S2, S3, S4, S5, S6, S7 = 4, 8, 12, 16, 24, 32, 48


@dataclass(frozen=True, slots=True)
class Metrics:
    """Control sizing for one density.

    A pill's radius must be half its own rendered height. This Qt build does not clamp an
    oversized radius to a capsule -- a radius past half the widget's height silently falls
    back to square corners -- so the radii here are measured against the padding and font
    beside them, and cannot be carried over to a different density.

    Attributes:
        font_pt: Base body size.
        small_pt: The secondary tier: notes, hints, versions, monospace.
        btn_pad: Vertical and horizontal padding for a stock ``QPushButton``. Its vertical
            half must equal ``pill_pad``'s, so a primary and a secondary button standing side by
            side are the same height -- the whole reason paper-gui used to carry its own ``#Btn``
            rule instead of the shared one.
        pill_pad: Padding for ``#Primary`` and ``#Danger``.
        pill_radius: Half of ``pill_height``.
        pill_height: The height ``#Primary`` actually renders at, measured on Windows at 96dpi
            with ``tools/measure_pills.py``. Recorded rather than computed: an arithmetic
            estimate of Qt's line box was wrong by 6px and shipped square-cornered chips.
        chip_pad: Padding for ``#Chip``.
        chip_radius: Half of ``chip_height``.
        chip_height: The height ``#Chip`` actually renders at, measured the same way.
    """

    font_pt: int
    small_pt: int
    btn_pad: tuple[int, int]
    pill_pad: tuple[int, int]
    pill_radius: int
    pill_height: int
    chip_pad: tuple[int, int]
    chip_radius: int
    chip_height: int

    def __post_init__(self) -> None:
        if self.btn_pad[0] != self.pill_pad[0]:
            raise ValueError(
                "btn_pad and pill_pad must share a vertical padding, or a plain button and a "
                f"pill next to it are different heights: {self.btn_pad} vs {self.pill_pad}")
        for what, radius, height in (("pill", self.pill_radius, self.pill_height),
                                     ("chip", self.chip_radius, self.chip_height)):
            if radius > height // 2:
                raise ValueError(
                    f"{what}_radius {radius} is past half of the {height}px it renders at, so Qt "
                    "draws square corners instead of a capsule; re-measure with "
                    "tools/measure_pills.py")

    @property
    def title_pt(self) -> int:
        """The display tier."""
        return round(self.font_pt * 1.9)

    @property
    def section_pt(self) -> int:
        """The section-heading tier."""
        return round(self.font_pt * 1.2)


COMPACT = Metrics(
    font_pt=10,
    small_pt=9,
    btn_pad=(9, 14),
    pill_pad=(9, 26),
    pill_radius=20,
    pill_height=40,
    chip_pad=(4, 13),
    chip_radius=14,
    chip_height=28,
)
"""A dense desktop tool, driven with a mouse at arm's length."""

COMFORTABLE = Metrics(
    font_pt=18,
    small_pt=14,
    btn_pad=(14, 26),
    pill_pad=(14, 34),
    pill_radius=32,
    pill_height=66,
    chip_pad=(8, 22),
    chip_radius=23,
    chip_height=46,
)
"""A full-screen operator window, read and driven from across a desk."""
