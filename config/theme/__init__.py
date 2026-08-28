# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Design tokens — every visual parameter the platform draws with (coding rule R7).

Colours, type sizes, spacing steps, corner radii and shadows are named here and
nowhere else. ``src/visual/theme_css.py`` serialises them into the ``:root`` block
and the ``window.__THEME`` object injected at the top of every console page; the
stylesheets and the panel scripts then refer to tokens rather than to values. An
adopting institution rebrands by changing this package, not by editing the front end.

Layout::

    _palette.py   BRAND, SURFACE, TEXT, RAG, STATE, HUE   — the chrome
    _scale.py     TYPE, SPACE, RADIUS, SHADOW             — the non-colour parameters
    _domain.py    PERIL, DEPTH, MAP, SIGN, SERIES         — physical-risk vocabulary
    registry.py   THEME, THEME_GROUPS                     — the flat view emitters use

See docs/refactor/theme_centralisation_plan.md for the migration this package is
step 1 of, and docs/rules/coding_rules.md R7 for the rule it exists to satisfy.
"""

from ._domain import DEPTH, MAP, PERIL, SERIES, SIGN
from ._palette import BRAND, HUE, RAG, STATE, SURFACE, TEXT
from ._scale import RADIUS, SHADOW, SPACE, TYPE
from .registry import SANCTIONED_PACKAGE, THEME, THEME_GROUPS

__all__ = [
    "BRAND", "SURFACE", "TEXT", "RAG", "STATE", "HUE",
    "TYPE", "SPACE", "RADIUS", "SHADOW",
    "PERIL", "DEPTH", "MAP", "SIGN", "SERIES",
    "THEME", "THEME_GROUPS", "SANCTIONED_PACKAGE",
]
