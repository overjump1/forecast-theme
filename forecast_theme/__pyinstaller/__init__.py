"""PyInstaller hook registration.

Declared through the ``pyinstaller40`` entry point in ``pyproject.toml``, so PyInstaller discovers
this directory automatically from the installed distribution. That is what lets a consuming app
bundle the fonts without adding a ``datas`` entry to its own ``.spec``.
"""

import os


def get_hook_dirs():
    return [os.path.dirname(__file__)]
