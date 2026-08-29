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

"""The theme endpoints: the token values, and what each status is drawn in.

Parity with MKM-ModelRisk, which serves the same two. ``/theme.css`` gives a browser the
token VALUES as a ``:root`` block; ``/api/theme`` gives it the MAPPING the JavaScript
needs — which token a rating, a trigger level or a lifecycle state is drawn in — so no
colour decision is written into a ``.js`` file.

The Folium console does not use these. It has its own front end inlined into the
document at assembly time, so ``visual.theme_css`` injects the same payload directly and
a fetch would be a slower way to get bytes the page already has. These exist for every
*other* surface: the standalone admin page, the CDM Asset Review tool, anything served as
its own document, and any external consumer that wants the palette. Both read the same
``config.theme``, so there is still one source — two deliveries of it, not two copies.

Read-only and unauthenticated by design: this carries configuration, not governance
data, and the same values are already visible in any served page.
"""

import hashlib

from flask import Blueprint, Response, jsonify

from config.theme import STATUS_COLOUR_DEFAULTS, STATUS_COLOUR_TOKENS, THEME
from visual.theme_css import theme_css

theme_bp = Blueprint("theme", __name__)

CSS_MIMETYPE = "text/css"


def theme_version() -> str:
    """A stamp for the current token values, for the ``?v=`` on a stylesheet link.

    The asset-version helpers cannot answer for this one: they watch file modification
    times under ``src/static``, and the theme is not a file there. Hashing the served
    text gives the same guarantee — the URL changes exactly when the bytes do, so a
    rebrand cannot be masked by a browser cache, and an unchanged theme keeps its cached
    copy across restarts.
    """
    return hashlib.sha256(theme_css().encode("utf-8")).hexdigest()[:12]


@theme_bp.route("/theme.css", methods=["GET"])
def get_theme_css():
    """The design tokens as a stylesheet."""
    return Response(theme_css(), mimetype=CSS_MIMETYPE)


@theme_bp.route("/api/theme", methods=["GET"])
def get_theme():
    """The tokens and the value→token ramps, for a front end that cannot use ``var()``."""
    return jsonify({
        "tokens": THEME,
        "status_colours": STATUS_COLOUR_TOKENS,
        "status_defaults": STATUS_COLOUR_DEFAULTS,
        "version": theme_version(),
    })
