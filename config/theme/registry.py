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

"""Canonical registry of the design tokens — the single source rule R7 points at.

The groups in :mod:`config.theme._palette`, :mod:`config.theme._scale` and
:mod:`config.theme._domain` organise the vocabulary for a reader. This flattens them
into the one mapping every emitter consumes: the ``:root`` block injected into the
console, the ``window.__THEME`` object the panel scripts read, and (from step 8) the
reportlab and matplotlib palettes the generated documents draw with.

It carries no rendering logic — the emitter is ``src/visual/theme_css.py``. This file
only *names* what exists, the same way ``config.path.registry`` names the filesystem
roots without resolving any of them, so the styling policy is data rather than
scattered string matching.

Token names are unique across the groups. The groups organise this package; they do
not namespace it, because a CSS custom property has one flat namespace and pretending
otherwise would let two groups define ``--line`` and leave the winner to file order.
``tests/config/test_theme.py`` holds that true.
"""

from ._domain import DEPTH, MAP, PERIL, SERIES, SIGN
from ._palette import BRAND, HUE, RAG, STATE, SURFACE, TEXT
from ._scale import RADIUS, SHADOW, SPACE, TYPE

# The groups in the order they are emitted, so the served ``:root`` block reads in
# the same order as the package and a diff of either is legible.
THEME_GROUPS = (
    ("brand", BRAND),
    ("surface", SURFACE),
    ("text", TEXT),
    ("rag", RAG),
    ("state", STATE),
    ("hue", HUE),
    ("peril", PERIL),
    ("depth", DEPTH),
    ("map", MAP),
    ("sign", SIGN),
    ("series", SERIES),
    ("type", TYPE),
    ("space", SPACE),
    ("radius", RADIUS),
    ("shadow", SHADOW),
)

# Every token, flat, keyed by custom-property name.
THEME = {name: value for _, group in THEME_GROUPS for name, value in group.items()}

# Package (relative to the repo root) that is the sanctioned home for *all* visual
# parameters. Modules under here are exempt from the styling audit — this is the one
# place a colour, a type size, a spacing step or a radius is allowed to be written
# down. The mirror of ``config.path.registry.SANCTIONED_PACKAGE`` for rule R7.
SANCTIONED_PACKAGE = "config/theme"

__all__ = ["THEME", "THEME_GROUPS", "SANCTIONED_PACKAGE"]
