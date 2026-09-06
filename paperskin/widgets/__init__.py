"""Widgets the stylesheet cannot express.

A knob that slides cannot be written in QSS, so it is painted from the palette instead. Anything in
here reads ``palette.active()`` at paint time rather than capturing a colour when it is built.
"""
