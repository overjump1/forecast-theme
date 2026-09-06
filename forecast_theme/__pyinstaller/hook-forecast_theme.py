"""Collect the bundled fonts, and the modules PyInstaller cannot see.

``collect_data_files`` places the fonts at ``forecast_theme/fonts/`` under ``_MEIPASS``, which is
exactly where ``styling.font_dir()`` looks first.

The hidden imports matter just as much. ``forecast_theme/__init__.py`` resolves its Qt-dependent
surface through a module ``__getattr__`` that calls ``importlib.import_module`` -- that is what
keeps the palette importable with no PyQt6 installed, and it is invisible to static analysis. An
app that only ever says ``forecast_theme.apply(...)`` therefore freezes without the module that
provides it, and dies on launch with

    ModuleNotFoundError: No module named 'forecast_theme.styling'

An app that happens to import ``forecast_theme.styling`` directly is fine, which is why this can
hold in one consumer and fail in the very next one. Listing them here fixes it once for everybody
rather than once per ``.spec``.
"""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("forecast_theme")

hiddenimports = [
    "forecast_theme.styling",
    "forecast_theme.platform",
    "forecast_theme.platform.win_glass",
    "forecast_theme.widgets",
    "forecast_theme.widgets.switch",
    # Not reached through __getattr__, but a consumer that generates its tokens as a build step
    # imports it by name only.
    "forecast_theme.export",
]
