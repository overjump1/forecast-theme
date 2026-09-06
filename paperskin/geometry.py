"""Geometry: the measurements that are identity rather than appearance.

Nothing here is per-mode. A radius is not an appearance -- a card is the same
shape in light and dark -- so these are plain module constants rather than
fields on ``Palette``.

Kept out of ``palette.py`` so that a palette stays purely about colour, and out
of ``sheet.py`` so that painting code can import a radius without pulling in the
stylesheet.
"""

from __future__ import annotations

# Not per-mode: a radius is not an appearance. The pill radii below are the slide's stadium, and
# the primary action uses one of them rather than RADIUS_CTRL.
#
# A pill's radius is exactly half its own height, not the oversized "999px" shorthand CSS engines
# usually clamp for you: this Qt build does not clamp it -- a radius past half the widget's real
# rendered height silently falls back to square corners instead of capping at a capsule, so a
# 999px radius on anything shorter than ~2000px draws a plain rectangle. Two sizes because the
# buttons wearing a pill come in two heights: the run/stop actions (padding 9px 26px, which comes
# to ~40px tall) and the small chips (padding 4px 13px, ~28px tall) -- if either padding changes,
# its radius needs re-measuring against the button's actual rendered height, not guessed.
RADIUS_PANEL = 14
RADIUS_CTRL = 8
RADIUS_PILL_LG = 20  # half of ~40px: the run/stop actions' rendered height
RADIUS_PILL = 14     # half of ~28px: the chips' rendered height

# ---------------------------------------------------------------------------- spacing
#
# A 4pt grid. Every margin, padding and gap in a consuming app should be one of
# these seven values rather than a number typed at the call site -- that is the
# whole reason it is a scale and not arithmetic.
S1, S2, S3, S4, S5, S6, S7 = 4, 8, 12, 16, 24, 32, 48
