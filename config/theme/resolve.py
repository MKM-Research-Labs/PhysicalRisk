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

"""Look a design token up from Python.

``THEME[token]`` already does this; :func:`colour` adds the one thing a bare subscript
cannot — an error that says what went wrong. A ``KeyError: 'acccent'`` from deep inside
a page builder tells you a dict lacked a key; this tells you a token does not exist and
where tokens live.

It is a plain string lookup with no rendering dependency, so anything may import it: a
Folium popup, a matplotlib figure, a CLI, a test. The reportlab ``Color`` wrapper is
``reports.theme_pdf.pdf_colour``, and it is over there because it needs reportlab and
this must not.
"""

from .registry import THEME


def colour(token: str) -> str:
    """The hex value of a design token.

    Raises on an unknown token rather than returning a default: an element drawn in a
    plausible wrong colour is the failure this whole package exists to prevent, and it
    is far harder to notice than an exception.
    """
    try:
        return THEME[token]
    except KeyError:
        raise KeyError(
            f"unknown design token {token!r}; see config/theme") from None


__all__ = ["colour"]
