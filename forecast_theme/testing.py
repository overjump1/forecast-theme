"""Reusable assertions, so every consumer checks the same promises the design makes.

Public API rather than a test file: a consuming app imports these into its own suite. Three kinds
of thing live here --

- **Colour maths** (``contrast``, ``over``, ``surfaces``) so an app can check its own tokens against
  its own surfaces, using the same arithmetic the package checks itself with.
- **``check_qss``**, a cheap structural check that an app's ``qss_extra()`` actually compiles.
- **Source scanners** (``inline_colour_stylesheets``, ``graphics_effects``) which read the
  *consuming* app's tree. These cannot live in the package's own suite -- there is nothing to scan
  there -- so they ship as functions each app points at itself.

Deliberately Qt-free, so a headless CI job can run all of it.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Collection, Iterable

from .palette import Ink, Palette





def linear(channel: int) -> float:
    c = channel / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgb(token) -> tuple[int, int, int]:
    """Channels for any of the three forms a colour arrives in.

    A tuple passes straight through, so a surface already resolved by ``surfaces()`` can be fed
    back into ``over()`` or ``contrast()`` without the caller unpacking it first -- which is
    what an app checking its own tokens against its own surfaces actually wants to do.
    """
    if isinstance(token, tuple):
        return token
    if isinstance(token, Ink):
        return token.r, token.g, token.b
    text = token.lstrip("#")
    return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def over(token, ground) -> tuple[int, int, int]:
    """A token composited over an opaque background, which is what the operator actually sees."""
    fr, fg, fb = rgb(token)
    br, bg, bb = rgb(ground)
    a = token.a if isinstance(token, Ink) else 1.0
    return (round(fr * a + br * (1 - a)),
            round(fg * a + bg * (1 - a)),
            round(fb * a + bb * (1 - a)))


def luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = (linear(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg, bg) -> float:
    """WCAG 2.x contrast ratio between two already-opaque colours."""
    a, b = luminance(rgb(fg)), luminance(rgb(bg))
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def surfaces(pal: Palette) -> dict[str, tuple[int, int, int]]:
    """The five opaque surfaces text can land on, resolved from the glass tokens.

    Recomputed rather than hardcoded, so tuning an alpha cannot silently invalidate the numbers
    the design is checked against.
    """
    return {
        "ground": rgb(pal.void),
        "card": over(pal.glass, pal.void),
        "recessed": over(pal.glass_low, pal.void),
        "raised": over(pal.glass_hi, pal.void),
        "popup": rgb(pal.depth),
    }


# The tiers, and what each one promises. Named here rather than in each app's suite so that the
# promise is a property of the design system, not of whoever wrote the test.
#
# Text that has to be read: WCAG AA for normal text.
READABLE = ("text", "text_dim", "ok", "warn", "danger", "accent_ink")
# Decoration and hints: the large-text / non-text floor, WCAG 1.4.11.
DECORATIVE = ("text_faint", "accent_line")

AA_NORMAL = 4.5
AA_LARGE = 3.0


def assert_readable_tiers(pal: Palette) -> None:
    """Every readable text tier clears 4.5:1 on every surface it can land on."""
    for token in READABLE:
        for where, ground in surfaces(pal).items():
            ratio = contrast(getattr(pal, token), ground)
            assert ratio >= AA_NORMAL, (
                f"{pal.name}: {token} on {where} is {ratio:.2f}:1, needs {AA_NORMAL}")


def assert_decorative_tiers(pal: Palette) -> None:
    """Faint text and thin accent graphics clear 3:1."""
    for token in DECORATIVE:
        for where, ground in surfaces(pal).items():
            ratio = contrast(getattr(pal, token), ground)
            assert ratio >= AA_LARGE, (
                f"{pal.name}: {token} on {where} is {ratio:.2f}:1, needs {AA_LARGE}")


# A tinted fill and the ink that lands on it. These are the pairings the base sheet actually
# creates -- a #BannerWarn holding a #Warn label, a checked #Chip, a tinted row -- and they are the
# tightest in the design, because a fill has to stay subtle while its own ink stays readable.
TINTED_PAIRS = (
    ("accent_fill", ("text", "accent_ink")),
    ("ok_fill", ("text", "ok")),
    ("warn_fill", ("text", "warn")),
    ("danger_fill", ("text", "danger")),
    ("ok_fill_hi", ("text", "ok")),
    ("warn_fill_hi", ("text", "warn")),
    ("danger_fill_hi", ("text", "danger")),
)


def assert_tinted_fills(pal: Palette) -> None:
    """Every ink the sheet puts on a tinted fill clears 4.5:1 over the card it sits on.

    Checked because it is the pairing most likely to drift: nudging a fill's alpha for looks moves
    a contrast ratio nobody was thinking about. The dark ``danger``/``danger_fill`` pair is the
    tightest of the eight and is why this test exists.
    """
    card = surfaces(pal)["card"]
    for fill, inks in TINTED_PAIRS:
        ground = over(getattr(pal, fill), card)
        for ink in inks:
            ratio = contrast(getattr(pal, ink), ground)
            assert ratio >= AA_NORMAL, (
                f"{pal.name}: {ink} on {fill} over card is {ratio:.2f}:1, needs {AA_NORMAL}")


def check_qss(sheet: str) -> None:
    """A cheap structural check that a stylesheet fragment is well formed.

    Qt does not report a stylesheet parse error -- it silently drops the rule it could not read, so
    a stray brace costs you every rule after it with no diagnostic at all. Hence checking the shape
    rather than trusting it.
    """
    assert sheet.count("{") == sheet.count("}"), (
        f"brace imbalance: {sheet.count('{')} open, {sheet.count('}')} close")
    assert "{pal." not in sheet, "an f-string placeholder survived into the sheet"
    assert not re.search(r":\s*(None|nan)\s*[;}]", sheet), "a token resolved to None"


def _iter_sources(root: Path) -> Iterable[Path]:
    for path in sorted(Path(root).rglob("*.py")):
        if "__pycache__" in path.parts or ".venv" in path.parts:
            continue
        yield path


def _parse(path: Path) -> ast.Module | None:
    """The file's syntax tree, or None if it will not parse.

    Scanners below read the tree rather than the text. A comment or a docstring that *mentions*
    QGraphicsDropShadowEffect -- to explain why it was removed, which is exactly the comment a
    codebase that got this right will have -- is prose, not a use, and a text scan cannot tell the
    difference.
    """
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return None


def _called_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def _literal_text(node: ast.AST) -> str:
    """Every string literal reachable inside an expression, joined.

    An f-string arrives as a JoinedStr whose constant parts are the literal text; the interpolated
    parts are expressions, and their source is recovered separately so that a call like
    ``setStyleSheet(f"color: {pal.text}")`` is still recognised as carrying a colour.
    """
    parts = []
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            parts.append(child.value)
        elif isinstance(child, ast.Attribute):
            parts.append(child.attr)
        elif isinstance(child, ast.Name):
            parts.append(child.id)
    return " ".join(parts)


# Palette field names that are colours. Used to spot a colour reaching an inline stylesheet through
# a variable rather than as a literal.
_COLOUR_HINTS = ("color:", "background:", "border-color:")


def inline_colour_stylesheets(root: Path, *, allow: Collection[str] = ()) -> list[str]:
    """Every ``setStyleSheet`` call in ``root`` that carries a colour.

    An inline stylesheet outranks the application stylesheet on that widget *permanently*, so a
    widget coloured that way can never be re-themed -- which also means it silently ignores every
    theme switch. Colour belongs in the application sheet, reached by object name or by the ``tone``
    dynamic property.

    A colourless inline sheet is not reported: making a scroll area's viewport transparent is the
    standard Qt idiom and has nothing to do with the palette.

    Args:
        root: The consuming package's source directory.
        allow: File *names* exempted. Keep this list as short as it can be, and write down why each
            entry is on it.

    Returns:
        ``"path:line: source"`` for each offender, ready to paste into an assertion message.
    """
    offenders = []
    for path in _iter_sources(root):
        if path.name in allow:
            continue
        tree = _parse(path)
        if tree is None:
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or _called_name(node) != "setStyleSheet":
                continue
            text = " ".join(_literal_text(arg) for arg in node.args)
            has_colour = (
                re.search(r"#[0-9A-Fa-f]{3,8}", text)
                or re.search(r"rgba?\(\s*\d", text)
                or any(hint in text for hint in _COLOUR_HINTS)
            )
            if has_colour:
                source = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""
                offenders.append(f"{path}:{node.lineno}: {source}")
    return offenders


_EFFECT_NAMES = frozenset({
    "setGraphicsEffect",
    "QGraphicsDropShadowEffect",
    "QGraphicsBlurEffect",
    "QGraphicsColorizeEffect",
    "QGraphicsOpacityEffect",
})


def graphics_effects(root: Path) -> list[str]:
    """Every ``QGraphicsEffect`` use in ``root``.

    On a window with any translucency Qt renders an effected widget through an offscreen cache and
    derives its damage region from the effect's bounding rect, which leaves ghosts of the previous
    frame behind. Depth comes from translucent fills and a one-pixel edge instead; a fade is a
    ``QVariantAnimation`` over a painted alpha, and an outer window shadow -- if an app has a
    frameless window that needs one -- is a cached ``QPixmap``.

    Reads the syntax tree, so the comment explaining why the effect was removed does not count as
    using one.
    """
    offenders = []
    for path in _iter_sources(root):
        tree = _parse(path)
        if tree is None:
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for node in ast.walk(tree):
            name = ""
            if isinstance(node, ast.Attribute):
                name = node.attr
            elif isinstance(node, ast.Name):
                name = node.id
            if name in _EFFECT_NAMES:
                source = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""
                offenders.append(f"{path}:{node.lineno}: {source}")
    return sorted(set(offenders))
