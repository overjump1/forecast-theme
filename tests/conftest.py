"""Shared fixtures.

Everything in this suite is headless -- nothing builds a widget, and PyQt6 need not even be
installed for most of it. That is a property of the package worth protecting: ``palette``,
``geometry``, ``sheet`` and ``testing`` import no Qt, so the contrast promises can be checked in
any CI job.
"""

from __future__ import annotations

import pytest

import paperskin

BOTH = pytest.mark.parametrize(
    "pal", [paperskin.LIGHT, paperskin.DARK], ids=["light", "dark"])

TILE_STATES = ("empty", "pending", "queued", "running", "done", "carried_over", "failed",
               "aborted")
