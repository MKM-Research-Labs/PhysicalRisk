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

"""Resolve design tokens into the colour objects the generated documents draw with.

The third emitter, beside ``src/visual/theme_css.py`` (the console's ``:root`` block)
and ``src/routes/theme.py`` (the ``/theme.css`` and ``/api/theme`` routes). Same single
source, a different edge: reportlab wants a ``Color`` instance and matplotlib wants a
string, and neither can read a CSS custom property.

**Why this is not in ``config.theme``.** The token table is data and must stay
importable by anything — the audit, a test, a CLI with no rendering stack present.
Putting ``colors.HexColor`` in it would make every consumer of a colour name depend on
reportlab. The dependency belongs at the edge that actually renders.

A caller that wants the plain hex — matplotlib, a Folium path option, an f-string —
wants ``config.theme.colour`` instead. It has no rendering dependency, so the console
does not acquire reportlab just to name a colour.

``docs/models`` imports this too. Those generators are report generators; they were
already importing reportlab, and the alternative was a second private palette, which is
precisely what ``docs/models/full_audit/_constants.py`` used to be.
"""

from functools import lru_cache

from reportlab.lib import colors

from config.theme import THEME


@lru_cache(maxsize=None)
def pdf_colour(token: str):
    """The reportlab ``Color`` for a design token.

    Memoised because a page builder asks for the same handful of colours once per row,
    and because reportlab compares Color instances by value — sharing one instance per
    token keeps table styles comparable.

    Raises on an unknown token rather than returning a default. A PDF drawn in a
    plausible wrong colour is worse than one that fails to build: the build failure is
    seen once, by the person who caused it, and the wrong colour is seen by whoever the
    document was sent to.
    """
    try:
        return colors.HexColor(THEME[token])
    except KeyError:
        raise KeyError(
            f"unknown design token {token!r}; see config/theme") from None


__all__ = ["pdf_colour"]
