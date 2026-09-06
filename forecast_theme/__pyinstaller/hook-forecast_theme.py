"""Collect the bundled fonts into the frozen bundle.

``collect_data_files`` places them at ``forecast_theme/fonts/`` under ``_MEIPASS``, which is exactly
where ``styling.font_dir()`` looks first.
"""

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("forecast_theme")
