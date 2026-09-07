"""The bool control: a track with a knob that slides, as drawn on slide 1 of the reference deck.

A ``QCheckBox`` styled through QSS was what this used to be, and it could only ever be a track that
changed colour -- ``::indicator`` is a single box, and there is no way to express "a circle that
moves to the other end" in a stylesheet. Since the toggle is the most common control in the
parameter list and the one the reference art is most specific about, it is painted here instead.

It is a ``QAbstractButton`` subclass, so the API ``param_row`` already used is unchanged:
``toggled``, ``setChecked``, ``isChecked``.

Two constraints inherited from ``theme``'s docstring:

- No ``QGraphicsEffect`` (rule 2). The slide animation is a ``QVariantAnimation`` over a painted
  offset, which is the same technique the module docstring prescribes for fades.
- The widget does not mirror in RTL. On the reference slide -- which is itself right-to-left --
  "on" puts the knob on the right, the same side as in a left-to-right interface. Direction is
  pinned so a Hebrew window does not silently reverse the meaning of the control's position.
"""

from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QRectF, QSize, Qt, QVariantAnimation, pyqtProperty
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QAbstractButton

from .. import palette as theme
from ..derive import mix

TRACK_W = 40
TRACK_H = 22
KNOB_INSET = 3
SLIDE_MS = 130

# The keyboard focus ring, and the padding that leaves room for it OUTSIDE the capsule. Two
# choices worth writing down: it is drawn outside rather than on the track, because on the track it
# would have to clear both track colours; and it is drawn in the mode's own ink rather than in the
# accent, because ACCENT_LINE and TRACK_ON are the same value in dark mode -- an apricot ring
# around an ON switch would merge into the capsule in exactly one of the two palettes. TEXT is the
# Windows 11 idiom and is the highest-contrast token the palette has, in both modes.
FOCUS_W = 2
FOCUS_PAD = 3


class ToggleSwitch(QAbstractButton):
    """A two-state switch. Checkable by construction; nothing else uses it unchecked."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # See the module docstring: the knob's side is meaning, not layout.
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.setFixedSize(TRACK_W + 2 * FOCUS_PAD, TRACK_H + 2 * FOCUS_PAD)

        self._offset = 1.0 if self.isChecked() else 0.0
        self._ready = False
        self._slide = QVariantAnimation(self)
        self._slide.setDuration(SLIDE_MS)
        self._slide.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._slide.valueChanged.connect(self._on_slide)
        self.toggled.connect(self._retarget)

    # ------------------------------------------------------------------ animation

    def _retarget(self, checked: bool) -> None:
        target = 1.0 if checked else 0.0
        # Before the first show the value is being seeded from the model, not changed by anyone, so
        # it jumps. Otherwise every ON row in the list would slide in on open.
        if not self._ready:
            self._slide.stop()
            self._offset = target
            self.update()
            return
        self._slide.stop()
        self._slide.setStartValue(float(self._offset))
        self._slide.setEndValue(target)
        self._slide.start()

    def _on_slide(self, value) -> None:
        self._offset = float(value)
        self.update()

    @pyqtProperty(float)
    def offset(self) -> float:
        """Knob position, 0 at the off end and 1 at the on end. Exposed for tests."""
        return self._offset

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._ready = True

    # ------------------------------------------------------------------ painting

    def sizeHint(self) -> QSize:
        return QSize(TRACK_W + 2 * FOCUS_PAD, TRACK_H + 2 * FOCUS_PAD)

    def paintEvent(self, event) -> None:
        pal = theme.active()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        radius = TRACK_H / 2
        track = QRectF(FOCUS_PAD, FOCUS_PAD, TRACK_W, TRACK_H)

        # Track and knob colours are computed from the core palette rather than read off their
        # own stored tokens: off is a muted step from the surface toward the ink, on is the
        # accent; the knob is always a near-white circle, deepened slightly when off.
        track_off = mix(pal.surface, pal.text, 0.35)
        knob_off = mix(pal.text, "#FFFFFF", 0.55)
        knob_on = mix(pal.text, "#FFFFFF", 0.92)

        # The two ends of the ramp, blended by the slide position, so the colour and the knob
        # arrive together instead of the fill snapping ahead of the movement.
        track_colour = _blend(QColor(track_off), QColor(pal.accent), self._offset)
        knob_colour = _blend(QColor(knob_off), QColor(knob_on), self._offset)
        if not self.isEnabled():
            track_colour.setAlphaF(0.4)
            knob_colour.setAlphaF(0.55)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_colour)
        painter.drawRoundedRect(track, radius, radius)

        knob_d = TRACK_H - 2 * KNOB_INSET
        travel = TRACK_W - 2 * KNOB_INSET - knob_d
        knob = QRectF(track.x() + KNOB_INSET + travel * self._offset,
                      track.y() + KNOB_INSET, knob_d, knob_d)

        # Keyboard focus, painted rather than styled: the widget takes StrongFocus and answers the
        # arrow keys, and QSS cannot draw a ring around a shape it does not know about -- so
        # without this the focused switch is indistinguishable from every other one, and Space
        # flips whichever it happens to be.
        if self.hasFocus():
            ring = QPen(QColor(pal.text))
            ring.setWidth(FOCUS_W)
            painter.setPen(ring)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            gap = FOCUS_PAD - FOCUS_W / 2
            painter.drawRoundedRect(track.adjusted(-gap, -gap, gap, gap),
                                    radius + gap, radius + gap)
            painter.setPen(Qt.PenStyle.NoPen)

        # A white knob on the apricot track is 2.06:1, so in light mode it gets a rim. State is
        # also carried by position, which is why this is a refinement rather than the whole signal.
        if not pal.dark and self._offset > 0.5:
            painter.setPen(QColor(pal.accent_ink))
        painter.setBrush(knob_colour)
        painter.drawEllipse(knob)

        painter.end()

    def keyPressEvent(self, event) -> None:
        """Space and Return toggle; the arrows set an absolute state.

        The arrows are what a screen-reader user reaches for on a switch, and unlike Space they
        say which state they mean -- so holding one does not flap the value.
        """
        key = event.key()
        if key in (Qt.Key.Key_Left, Qt.Key.Key_Right):
            self.setChecked(key == Qt.Key.Key_Right)
            event.accept()
            return
        super().keyPressEvent(event)


def _blend(a: QColor, b: QColor, t: float) -> QColor:
    """Linear interpolation between two colours, clamped."""
    t = 0.0 if t < 0.0 else 1.0 if t > 1.0 else t
    return QColor(
        round(a.red() + (b.red() - a.red()) * t),
        round(a.green() + (b.green() - a.green()) * t),
        round(a.blue() + (b.blue() - a.blue()) * t),
    )
