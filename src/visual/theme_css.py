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

"""Serialise the design tokens into the block every console page opens with.

``config.theme`` holds the values; this renders them as a ``:root`` custom-property
block and pairs it with ``src/static/js/theme.js``, which reads them back. The result
is injected by :meth:`InteractivityManager.setup_map_interactivity` as the first element
on the map root, ahead of every panel's own inlined CSS.

Injecting first is not what makes ``var()`` resolve — custom properties are resolved
at computed-value time, so a reference in an earlier block still finds a ``:root``
defined later. It is about the cascade: a token defined here can be deliberately
overridden by a panel that redefines it further down, and never the other way round.
That is the ordering a themed page wants, and it is the reason the injection belongs
at the top of the seam rather than anywhere convenient.

It writes no rules and no selectors of its own — only ``--name: value;`` pairs — so
the stylesheets stay in ``src/static/css`` and this stays a serialiser of
configuration.

**Why one payload rather than two.** MKM-ModelRisk serves its tokens twice: a
``/theme.css`` route for the stylesheet and a ``/api/theme`` endpoint for the
JavaScript. It has to, because its front end is fetched separately from its page. Ours
is inlined into the document at assembly time, so a second copy would buy nothing and
risk the two disagreeing. ``theme.js`` therefore reads the values back off the
``:root`` block with ``getComputedStyle`` and memoises them — which also keeps this
module free of any JavaScript, and leaves the browser's own cascade as the single
authority on what a token resolves to.
"""

import json

from config.theme import (
    STATUS_COLOUR_DEFAULTS, STATUS_COLOUR_TOKENS, THEME, THEME_GROUPS,
)

#: The element id carried by the injected ``<style>``, so a test — or a person with
#: the inspector open — can find the block and confirm the page was themed.
THEME_STYLE_ID = "mkm-theme-tokens"


def theme_css() -> str:
    """The design tokens as a ``:root`` custom-property block.

    Grouped and commented in the order of :data:`config.theme.THEME_GROUPS`, so the
    block a browser shows reads the same way the config package does and a diff of
    either is legible.
    """
    lines = [":root {"]
    for label, group in THEME_GROUPS:
        lines.append(f"  /* {label} */")
        lines.extend(f"  --{name}: {value};" for name, value in group.items())
    lines.append("}")
    return "\n".join(lines) + "\n"


def theme_status_js() -> str:
    """The value→token ramps, as the object ``theme.js`` reads them.

    Token *names*, not colours. The browser resolves them against the ``:root`` block
    through ``Theme.status()``, which keeps this the same single payload as everything
    else here — there is no second copy of the palette to drift.

    All three families are emitted together — the modelled world
    (``config.theme._status``), the vocabulary shared with MKM-ModelRisk
    (``config.theme._governance``) and this platform's own console states
    (``config.theme._badges``). The front end does not care which is which; it asks for
    a ramp by name. The per-ramp fallback tokens travel with them, so an unrecognised
    value resolves the same way in the browser as it does in Python.
    """
    payload = {"ramps": STATUS_COLOUR_TOKENS, "defaults": STATUS_COLOUR_DEFAULTS}
    return f"window.__THEME_STATUS = {json.dumps(payload, sort_keys=True)};"


def theme_html() -> str:
    """The ``<style>`` and ``<script>`` pair that themes a page.

    Injected once per document. The style block comes first because ``theme.js`` reads
    the properties back off the cascade: it must be parsed before the script runs.
    """
    # Deferred: the asset loader lives inside ``visual.interactivity``, whose
    # package __init__ imports the manager, which imports this module. Importing it
    # at module scope would close that loop. The loader is a generic static-asset
    # reader with no interactivity dependency of its own and wants relocating a level
    # up; until it moves, reading it here keeps §4.9 at zero cycles.
    from .interactivity._jsbundle import js_static

    return (
        f'<style id="{THEME_STYLE_ID}">\n{theme_css()}</style>\n'
        f"<script>{theme_status_js()}\n{js_static('theme.js')}</script>\n"
    )


def token_names() -> tuple:
    """Every token the emitted block defines, for the audit and its tests."""
    return tuple(THEME)


__all__ = ["THEME_STYLE_ID", "theme_css", "theme_html", "theme_status_js",
           "token_names"]
