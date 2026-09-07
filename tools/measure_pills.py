"""Measure the real rendered height of each pill at each density.

Run this on a real desktop -- not offscreen, whose font metrics differ by up to 9px -- and copy
the numbers into the ``pill_height`` and ``chip_height`` fields of the presets in geometry.py.
Those fields exist because Qt does not clamp an oversized border-radius to a capsule: it
silently falls back to square corners, and an arithmetic estimate of Qt's line box was wrong
enough to ship exactly that.

    python tools/measure_pills.py
"""

from PyQt6.QtWidgets import QApplication, QPushButton

import forecast_theme as ft
from forecast_theme import styling

app = QApplication(["measure"])
faces = styling.load_fonts()

for name, metrics in (("COMPACT", ft.COMPACT), ("COMFORTABLE", ft.COMFORTABLE)):
    ft.use(ft.DARK)
    styling.apply(app, faces, glass=False, metrics=metrics)
    for label, obj, radius in (("Primary", "Primary", metrics.pill_radius),
                               ("Chip", "Chip", metrics.chip_radius)):
        btn = QPushButton("Sample")
        btn.setObjectName(obj)
        btn.ensurePolished()
        height = btn.sizeHint().height()
        half = height // 2
        flag = "SQUARE CORNERS" if radius > half else "ok"
        print(f"{name:12} {label:8} height={height:3} half={half:3} radius={radius:3}  {flag}")
        btn.deleteLater()
