# paperskin

The shared design system: one palette, one stylesheet, one set of contrast guarantees, for every
app in the family.

```python
from PyQt6.QtWidgets import QApplication
import paperskin

app = QApplication(sys.argv)
faces = paperskin.load_fonts()                    # once per process, never per restyle
paperskin.use(paperskin.resolve_theme(mode))      # mode is "system" | "light" | "dark"
paperskin.apply(app, faces, glass=True, extra=my_app_qss(paperskin.active()))
```

## The one mistake everybody makes

**A colour read at construction time does not follow a later `use()`.**

A module-level `QColor`, a dict of colour strings built at import, a matplotlib artist, a THREE.js
material — all of them survive a theme change *and* a window rebuild, still wearing whichever
palette happened to be active when they were built. The symptom is a widget that stays dark after
switching to light, and it is invisible until someone actually flips the theme.

Read colours inside `paintEvent` via `paperskin.active()`, or re-read them in a `restyle()` hook.
Everything here is shaped to make that the easy path — which is also why the palette is a value
passed around rather than a set of module globals that `use()` rebinds.

## What is shared and what is yours

`base_qss()` styles stock Qt classes plus the object names in `CONTRACT_NAMES`:

| Group | Names |
|---|---|
| Type scale | `Title` `Section` `Eyebrow` `Dim` `Faint` `Error` `Warn` `Mono` |
| Surfaces | `Card` `Rule` `Banner` `BannerWarn` `BannerError` |
| Buttons | `Primary` `Danger` `Ghost` `Chip` |

Plus the `[tone="..."]` dynamic property, for severity and outcome colours.

Anything specific to one app — its own widgets, its own dynamic properties — goes in that app's own
`qss_extra()`, appended after the base sheet:

```python
app.setStyleSheet(paperskin.base_qss(pal, ...) + "\n" + qss_extra(pal))
```

QSS is last-wins at equal specificity, so appending is a real override mechanism as well as an
extension one.

### The specificity trap

Qt follows CSS2 specificity, so `QLabel[tone="warn"]` **loses** to `QLabel#Section`. The base sheet
covers its own type-scale names. If your app's stylesheet gives a colour to `QLabel#CardName`, you
must cover it too:

```python
qss_extra = ... + paperskin.tone_rules(pal, hosts=("#CardName", "#RowTitle"))
```

This fails silently — a toned label simply keeps the wrong colour — so each app should test that
every locally-coloured `QLabel` name appears in its host list.

## Rules the sheet keeps

1. **No universal `QWidget { background }`.** It makes glass impossible: every child paints itself
   opaque, so a translucent window has nothing to show through.
2. **No `QGraphicsEffect` anywhere in a consuming tree.** On a translucent window Qt renders an
   effected widget through an offscreen cache and derives damage from the effect's bounding rect,
   leaving ghost frames. Use a `QVariantAnimation` over a painted alpha, and a cached `QPixmap` for
   an outer window shadow. `paperskin.testing.graphics_effects(root)` checks this.
3. **Never letter-space Hebrew.** It breaks the visual join between letters and reads as a
   rendering fault. Hierarchy comes from size, weight and colour.
4. **Font sizes in `pt`, never `px`.** Qt scales `pt` by font DPI and `px` only by
   device-pixel-ratio, so a mixed sheet does not scale together under the Windows text-size setting.

## Testing your app against the design

`paperskin.testing` is public API, not a test file:

```python
from pathlib import Path
from paperskin import testing

def test_no_inline_colour_stylesheets():
    assert not testing.inline_colour_stylesheets(Path("myapp"), allow={"theme_ext.py"})

def test_no_graphics_effects():
    assert not testing.graphics_effects(Path("myapp"))

def test_my_extra_sheet_compiles():
    for pal in (paperskin.LIGHT, paperskin.DARK):
        testing.check_qss(qss_extra(pal))
```

`contrast()`, `over()`, `surfaces()` and `rgb()` are there too, so an app can check its own tokens
against its own surfaces with the same arithmetic the package checks itself with.

## Fonts

Heebo (body), Rubik (display) and JetBrains Mono, plus Alef — all SIL OFL, bundled and registered by
`load_fonts()`. Hebrew is the constraint that picks them: the field of modern Hebrew-capable faces
is small, and Heebo and Rubik are the two with real Hebrew design rather than Latin shapes with
Hebrew bolted on.

The package ships a PyInstaller hook, so **a consuming app's `.spec` needs no `datas` entry for
fonts**. A font-less bundle degrades silently to a system fallback, so verify once per app that the
frozen build really contains `paperskin/fonts/Heebo.ttf` rather than trusting it.

## Versioning

Pin by tag. In each consumer's `requirements.txt`:

```
paperskin @ git+https://github.com/overjump1/paperskin@v1.0.0
```

For an environment that cannot reach GitHub, that one line points at an internal clone instead;
nothing else differs.

| Bump | Means |
|---|---|
| **major** | A `Palette` field removed or renamed; a `CONTRACT_NAMES` entry removed or redefined; a signature change in `apply`/`base_qss`/`load_fonts`. |
| **minor** | A new token, a new contract selector, **or any change to a colour value.** |
| **patch** | Non-visual fixes only. |

Colour changes are **minor, never patch**. A "patch" that silently changes what an operator sees is
exactly the class of change a pinned dependency exists to prevent.

Adding a `Palette` field is safe for consumers (nothing outside this package constructs a palette);
renaming or removing one is breaking.

## Development

```bash
pip install -e ".[dev]"
pytest
```

The suite is headless — nothing builds a widget. `palette`, `geometry`, `sheet` and `testing`
import no Qt at module scope, which is what lets the contrast promises be checked in any CI job,
and `test_packaging.py` asserts that stays true.
