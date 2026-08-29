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

"""Rewrite the front end's colour literals as token references.

The mechanical half of step 6. :mod:`literal_scan` says which token each literal should
be and whether the site can take a ``var()``; this does the rewriting, and does it only
where the scan is confident.

**It edits inside string literals, not whole lines.** A single line of this console
routinely mixes contexts::

    ctx.fillStyle = '#c62828'; el.style.color = '#333';

Replacing every ``#hex`` on that line would put a ``var()`` into ``fillStyle``, where the
CSS parser never sees it and the canvas silently draws black. So each quoted string is
judged on its own, and only strings that are CSS get touched.

Anything the scan marks ``js_value`` or ``review`` is left alone and reported. Those are
converted by hand: a Chart.js option needs ``Theme.value('token')``, and a variable
assigned by a ternary needs its *use* traced before anyone can say which it is.
"""

import re

from literal_scan import HEX, _CSS_CONTEXT, _CSS_DECLARATION, _STRINGS, classify


def convert_line(line, tokens_by_literal):
    """Rewrite the CSS-context colour literals on one line. Returns (line, count)."""
    if not HEX.search(line):
        return line, 0

    changed = 0

    def in_string(match):
        nonlocal changed
        string = match.group(0)
        if not _CSS_DECLARATION.search(string):
            return string

        def swap(hit):
            nonlocal changed
            token = tokens_by_literal.get(hit.group(0).lower())
            if token is None:
                return hit.group(0)
            changed += 1
            return f"var(--{token})"

        return HEX.sub(swap, string)

    rewritten = _STRINGS.sub(in_string, line)

    # ``el.style.color = '#333'`` — the string is bare, so the line is the only
    # evidence. These take Theme.value(), not var(): a browser accepts a var() through
    # the CSSOM but jsdom's stricter implementation validates the value against the
    # property's type and silently drops it, so every unit test reading the property
    # back sees an empty string. Theme.value() returns a real hex, which every context
    # accepts, and removes the question of how faithfully a given CSSOM implements
    # custom properties.
    if not changed and _CSS_CONTEXT.search(line) and classify(line) == "css":
        def swap_bare(hit):
            nonlocal changed
            token = tokens_by_literal.get(hit.group(0).lower())
            if token is None:
                return hit.group(0)
            changed += 1
            return f"Theme.value('{token}')"

        rewritten = HEX.sub(swap_bare, rewritten)
        rewritten = re.sub(r"""['"](Theme\.value\('[a-z0-9-]+'\))['"]""", r"\1",
                           rewritten)

    return rewritten, changed


def convert_file(path, tokens_by_literal):
    """Rewrite one file in place. Returns the number of literals converted."""
    original = path.read_text(encoding="utf-8")
    out, total = [], 0
    for line in original.splitlines(keepends=True):
        body = line.rstrip("\n")
        newline = line[len(body):]
        rewritten, count = convert_line(body, tokens_by_literal)
        out.append(rewritten + newline)
        total += count
    if total:
        path.write_text("".join(out), encoding="utf-8")
    return total


__all__ = ["convert_file", "convert_line"]
