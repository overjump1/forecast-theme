"""forecast_theme -- the shared design system.

One palette, one stylesheet, one set of contrast guarantees, for every app in the family.

Typical use, once per process::

    from PyQt6.QtWidgets import QApplication
    import forecast_theme

    app = QApplication(sys.argv)
    faces = forecast_theme.load_fonts()                       # once, never per restyle
    forecast_theme.use(forecast_theme.resolve_theme(mode))         # mode is "system"/"light"/"dark"
    forecast_theme.apply(app, faces, glass=True, extra=my_app_qss(forecast_theme.active()))

**The one mistake everybody makes.** A colour read at construction time does not follow a later
``use()``. A module-level ``QColor``, a dict of colour strings built at import, a THREE.js material
or a matplotlib artist created once -- all of them survive a theme change and even a window rebuild,
still wearing the palette that happened to be active when they were built. Read colours inside
``paintEvent`` via ``active()``, or re-read them in a ``restyle()`` hook. Everything in this package
is shaped to make that the easy path.
"""

from __future__ import annotations

from . import export, testing
from .geometry import (
    RADIUS_CTRL,
    RADIUS_PANEL,
    RADIUS_PILL,
    RADIUS_PILL_LG,
    S1,
    S2,
    S3,
    S4,
    S5,
    S6,
    S7,
)
from .palette import (
    DARK,
    LIGHT,
    MODE_DARK,
    MODE_LIGHT,
    MODE_SYSTEM,
    MODES,
    PALETTES,
    Ink,
    Palette,
    Tone,
    active,
    qc,
    resolve,
    token_names,
    use,
)
from .sheet import CONTRACT_NAMES, base_qss, tone_rules

__version__ = "0.3.0"

__all__ = [
    # palette
    "Ink", "Palette", "Tone", "LIGHT", "DARK", "PALETTES",
    "MODE_LIGHT", "MODE_DARK", "MODE_SYSTEM", "MODES",
    "active", "use", "resolve", "token_names", "qc",
    # geometry
    "RADIUS_PANEL", "RADIUS_CTRL", "RADIUS_PILL_LG", "RADIUS_PILL",
    "S1", "S2", "S3", "S4", "S5", "S6", "S7",
    # sheet
    "base_qss", "tone_rules", "CONTRACT_NAMES",
    # non-Qt surfaces
    "testing", "export",
    "__version__",
]


# The Qt-dependent surface, resolved on first use. ``importlib.import_module`` rather than
# ``from . import styling``: the latter re-enters this very function looking for the attribute it
# is trying to create, which recurses until the stack runs out.
_LAZY_MODULES = {
    "styling": ".styling",
    "win_glass": ".platform.win_glass",
}

_LAZY_ATTRS = {
    name: ".styling" for name in (
        "Faces", "load_fonts", "apply", "set_tone", "repolish",
        "system_prefers_light", "resolve_theme", "font_dir",
    )
}
_LAZY_ATTRS["ToggleSwitch"] = ".widgets.switch"


def __getattr__(name: str):
    """Expose the Qt-dependent surface lazily.

    ``palette``, ``geometry``, ``sheet`` and ``testing`` are Qt-free, so importing this package
    costs nothing and works headless -- which is what lets a token generator or a contrast check
    run in an interpreter with no PyQt6 at all. ``styling``, ``win_glass`` and ``ToggleSwitch``
    import Qt, so they are resolved on first use instead of at import.

    Resolved modules are cached into ``globals()``, so this runs once per name per process.
    """
    import importlib

    if name in _LAZY_MODULES:
        module = importlib.import_module(_LAZY_MODULES[name], __name__)
        globals()[name] = module
        return module
    if name in _LAZY_ATTRS:
        module = importlib.import_module(_LAZY_ATTRS[name], __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
