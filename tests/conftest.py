"""Shared fixtures.

Everything in this suite is headless -- nothing builds a widget, and PyQt6 need not even be
installed for most of it. That is a property of the package worth protecting: ``palette``,
``geometry``, ``sheet`` and ``testing`` import no Qt, so the contrast promises can be checked in
any CI job.
"""

from __future__ import annotations

import pytest

import forecast_theme

BOTH = pytest.mark.parametrize(
    "pal", [forecast_theme.LIGHT, forecast_theme.DARK], ids=["light", "dark"])
