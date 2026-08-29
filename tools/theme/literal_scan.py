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

"""Find colour literals in the front end, and say which token each one should be.

This is the tooling step 6 of docs/refactor/theme_centralisation_plan.md needs to be
systematic rather than a 3,000-line find-and-replace done by eye. Step 5 will wire the
same scan into the audit as a gate; this is the part of it that has to exist first,
because you cannot convert what you cannot enumerate.

**Why a colour distance and not string equality.** 144 distinct literals appear in
``src/static/js``, and most are the same handful of colours written slightly
differently — ``#FFF`` and ``#ffffff``, ``#333`` and ``#333333``, and a long tail of
tints a designer would not distinguish. Matching in CIE Lab rather than by string means
a literal 1 ΔE from an existing token uses that token instead of minting a near-duplicate,
which is how a palette stays a palette. The threshold is deliberately tight: 1.5 ΔE is
below what anyone can see on adjacent flat colours, so a conversion at or under it moves
no pixel a person could detect.

**Why context matters more than the colour.** A hex in ``style="color:#333"`` becomes a
CSS declaration and can be ``var(--text)``. The identical hex in a Chart.js dataset or a
Leaflet path option is a JavaScript value that never reaches the CSS parser, and
``var(--text)`` there renders as nothing — Chart.js draws black, Leaflet draws its own
default. Those sites need ``Theme.value('text')``. Telling the two apart is the whole
difficulty of step 6, so the classifier below is conservative: anything it cannot place
with confidence is reported as ``review`` and converted by hand.
"""

import re
from pathlib import Path

#: A hex colour literal. Three- and six-digit only; ``#RRGGBBAA`` does not appear here.
#: The negative lookbehind rejects HTML numeric entities — ``&#128196;`` is a document
#: icon, not a colour, and the audit reporting six of them as literals would be a
#: backlog that can never reach zero.
HEX = re.compile(r"(?<!&)#[0-9a-fA-F]{3}\b|(?<!&)#[0-9a-fA-F]{6}\b")

#: A CSS declaration inside a string: ``color:#333;``, ``border:1px solid #ddd;``. The
#: property names are the ones the console actually builds style strings from.
_CSS_DECLARATION = re.compile(
    r"(?:background|background-color|color|border|border-top|border-bottom|border-left"
    r"|border-right|border-color|outline|box-shadow|fill|stroke|text-shadow)"
    r"\s*:\s*[^;\"\']*#[0-9a-fA-F]{3,6}")

#: The quoted string literals on a line, so a hex can be judged by the string it lives
#: in rather than by its neighbours 60 characters away.
_STRINGS = re.compile(r"'[^']*'|\"[^\"]*\"")

#: Below this ΔE, a literal is treated as the token it is nearest to. See the module
#: docstring: 1.5 is comfortably inside the just-noticeable difference for flat colour.
NEAR_DELTA_E = 1.5

#: Contexts where a hex becomes a CSS declaration, so ``var(--token)`` resolves.
_CSS_CONTEXT = re.compile(
    r"""style\s*=            # style="..." in an HTML string
      | \.style\.\w+\s*=     # el.style.color = '#333'
      | \.style\.setProperty
      | cssText
      | <style
    """, re.X)

#: Contexts where a hex is a JavaScript value the CSS parser never sees. ``var()`` is
#: silently wrong in all of them, so they take ``Theme.value(...)``.
_JS_VALUE_CONTEXT = re.compile(
    r"""backgroundColor | borderColor | pointBackgroundColor | pointBorderColor
      | fillColor | strokeColor | \bfillStyle | \bstrokeStyle
      | addColorStop | createLinearGradient
      | \bL\.(?:circle|polyline|polygon|marker|geoJSON)
      | gridColor | tickColor | \bcolor:\s*function
    """, re.X)


def _rgb(value):
    """A hex string as an (r, g, b) triple, expanding the three-digit form."""
    digits = value.lstrip("#").lower()
    if len(digits) == 3:
        digits = "".join(c * 2 for c in digits)
    return tuple(int(digits[i:i + 2], 16) for i in (0, 2, 4))


def _lab(colour):
    """sRGB to CIE Lab (D65). Enough precision to rank perceptual closeness."""
    red, green, blue = (channel / 255 for channel in colour)

    def linear(channel):
        return (channel / 12.92 if channel <= 0.04045
                else ((channel + 0.055) / 1.055) ** 2.4)

    red, green, blue = linear(red), linear(green), linear(blue)
    x = red * 0.4124 + green * 0.3576 + blue * 0.1805
    y = red * 0.2126 + green * 0.7152 + blue * 0.0722
    z = red * 0.0193 + green * 0.1192 + blue * 0.9505

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    fx, fy, fz = f(x / 0.95047), f(y), f(z / 1.08883)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e(first, second):
    """Perceptual distance between two hex colours (CIE76)."""
    a, b = _lab(_rgb(first)), _lab(_rgb(second))
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def nearest_token(literal, tokens):
    """The token closest to *literal*, as ``(name, delta_e)``."""
    return min(((name, delta_e(literal, value)) for name, value in tokens.items()),
               key=lambda pair: pair[1])


def classify(line, literal=None):
    """Where a literal ends up: ``css``, ``js_value`` or ``review``.

    Judged on the *string literal* the colour sits in, not on the whole line. The
    console builds its markup by concatenating fragments across many lines, so the
    ``style=`` that makes a fragment CSS is routinely nowhere near the colour:

        html += '<div style="padding:8px;' +
                'border-bottom:1px solid #ddd;background:#fafafa;" >' + …

    Both hexes on the second line are CSS, and a line-level test cannot see it. What
    *can* see it is that each sits inside a string containing a complete CSS
    declaration — ``border-bottom:1px solid #ddd`` — which a Chart.js option never does.

    ``js_value`` still wins a tie: a line carrying both a style string and a chart
    option is ambiguous, and guessing ``css`` there produces exactly the silent failure
    this exercise exists to prevent.
    """
    if _JS_VALUE_CONTEXT.search(line):
        return "js_value"
    if literal is not None:
        for string in _STRINGS.findall(line):
            if literal in string and _CSS_DECLARATION.search(string):
                return "css"
    if _CSS_CONTEXT.search(line):
        return "css"
    return "review"


def scan(root, tokens):
    """Every colour literal under *root*, with its nearest token and its context.

    Yields dicts so a caller can group them however it needs — by file for conversion,
    by token for review, by context for counting.
    """
    for path in sorted(Path(root).rglob("*.js")):
        if path.name == "theme.js":
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for literal in HEX.findall(line):
                name, distance = nearest_token(literal.lower(), tokens)
                yield {
                    "path": path,
                    "line": number,
                    "literal": literal,
                    "token": name if distance < NEAR_DELTA_E else None,
                    "delta_e": distance,
                    "context": classify(line, literal),
                }


__all__ = ["HEX", "NEAR_DELTA_E", "classify", "delta_e", "nearest_token", "scan"]
