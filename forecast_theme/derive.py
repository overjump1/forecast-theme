"""Derived colours: turning the minimal core palette into the fills, hovers and hairlines
that used to be separate stored tokens.

The palette itself carries only the handful of colours that are a real design decision --
``bg``, ``surface``, ``border``, ``text``, ``text_dim``, ``accent``, ``accent_ink``, ``ok``,
``warn``, ``danger``. Everything a stylesheet or a painted widget needs beyond that -- a
hover tint, a translucent fill, the ink that reads on a solid accent button -- is computed
here, at the point of use, from those core colours. That is what keeps the palette small
without losing any of the visual vocabulary the shared sheet used to bake in as named
fields: a hover state is ``alpha(pal.text, 0.06)`` instead of a ``ctrl_hover`` token nobody
could trace back to "text at low alpha".

Deliberately Qt-free, like the rest of the core, so it can be imported by the JS-facing
``export`` module and by a headless contrast test.
"""

from __future__ import annotations

from .palette import Ink


def _channels(hexcolor: str) -> tuple[int, int, int]:
    text = hexcolor.lstrip("#")
    return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def alpha(hexcolor: str, a: float) -> Ink:
    """``hexcolor`` at alpha ``a``, as the translucent value QSS and CSS both want."""
    r, g, b = _channels(hexcolor)
    return Ink(r, g, b, a)


def mix(a: str, b: str, t: float) -> str:
    """Linear channel interpolation between two hex colours, clamped to ``[0, 1]``.

    Plain RGB lerp, not a perceptual blend -- the same technique
    ``widgets/switch.py`` already used for its slide, kept here as the one shared
    implementation so a hover shade and a slide tint cannot drift apart.
    """
    t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
    ar, ag, ab = _channels(a)
    br, bg, bb = _channels(b)
    r = round(ar + (br - ar) * t)
    g = round(ag + (bg - ag) * t)
    bl = round(ab + (bb - ab) * t)
    return f"#{r:02x}{g:02x}{bl:02x}"


def _luminance(hexcolor: str) -> float:
    def linear(channel: int) -> float:
        c = channel / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = _channels(hexcolor)
    return 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b)


def shade(hexcolor: str, *, dark: bool, t: float = 0.18) -> str:
    """A hover/pressed step for ``hexcolor``: deepened in light mode, lightened in dark mode.

    Kept here rather than as a literal ``"#000000"``/``"#FFFFFF"`` in ``sheet.py`` -- that module's
    own test asserts it contains no colour literals of its own, so any mode-direction constant like
    this one belongs in the derive layer instead.
    """
    return mix(hexcolor, "#FFFFFF" if dark else "#000000", t)


def ink_on(hexcolor: str, *, light_ink: str = "#0B1220", dark_ink: str = "#F8FBFF") -> str:
    """Whichever fixed ink reads better on a solid ``hexcolor`` fill.

    For the one case a stylesheet cannot avoid: text sitting on a solid accent or status
    colour rather than on the page ground, where the mode's own ``text``/``accent_ink``
    tokens are not guaranteed to clear contrast (the accent is deliberately close to
    ``text`` in dark mode, for instance).
    """
    def contrast(fg: str, bg: str) -> float:
        a, b = _luminance(fg), _luminance(bg)
        hi, lo = max(a, b), min(a, b)
        return (hi + 0.05) / (lo + 0.05)

    return light_ink if contrast(light_ink, hexcolor) >= contrast(dark_ink, hexcolor) else dark_ink
