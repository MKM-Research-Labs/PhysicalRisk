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

"""Rewrite pixel values in inline styles as scale-token references (step 7).

The colour half of the migration is done; this is the rest of rule R7. A ``font-size``
or a ``border-radius`` written as a number is the same problem a hex was: an adopter
cannot make the console denser or rounder without editing the front end.

**Off-ladder values round half up.** A value that is not a rung and sits within 1px of
one takes that rung — 3px becomes 4px, 9px becomes 10px. Ties round up rather than down
because a cramped interface is a worse failure than a slightly loose one, and because a
consistent rule beats a per-case judgement nobody can reproduce later. Values further
than 1px from any rung are not roundable and are left alone; if there are many of them,
the scale is missing a rung and should gain one rather than the sites being bent to fit.

**Only CSS declarations are rewritten.** ``padding:8px 16px`` inside a style string
becomes ``padding:var(--space-4) var(--space-8)``, which the browser resolves. The same
number in ``chart.options.barThickness`` is a JavaScript integer, and a ``var()`` there
is not a length — it is a string, and the chart silently draws nothing. So the patterns
below are anchored to a CSS property name, never to a bare number.
"""

import re

#: The CSS properties whose pixel values this rewrites, and the token family each takes.
#: Anchoring to the property name is what keeps a bare number in JavaScript out of scope.
FONT_SIZE = re.compile(r"(font-size\s*:\s*)(\d+)px")
#: ``border-radius`` takes a shorthand too — ``border-radius:0 0 8px 8px`` rounds only
#: the bottom corners — so it is parsed as a list like spacing, not as one number.
RADIUS = re.compile(r"(border-radius\s*:\s*)([^;\"'}}]+)")
#: The whole declaration value, up to its delimiter, so a mixed list like
#: ``padding:2px 0`` is seen entire. Matching only the ``2px`` and substituting for it
#: yields ``padding:var(--space-1)0`` — the separating space is inside the match and is
#: lost with it, and the result is not a declaration at all. A shorthand has to be
#: rewritten as a unit or left alone.
SPACING = re.compile(
    r"((?:margin|padding|gap|row-gap|column-gap)"
    r"(?:-top|-right|-bottom|-left)?\s*:\s*)([^;\"'}}]+)")


def _rungs(group, prefix=None):
    """``{pixels: token}`` for a scale group, so a value can find its rung."""
    return {int(value.removesuffix("px")): name
            for name, value in group.items()
            if value.endswith("px") and (prefix is None or name.startswith(prefix))}


def snap(pixels, rungs):
    """The token for *pixels*, rounding half up to a rung within 1px. None if further."""
    if pixels in rungs:
        return rungs[pixels]
    for candidate in (pixels + 1, pixels - 1):     # +1 first: ties round up
        if candidate in rungs:
            return rungs[candidate]
    return None


def convert_text(text, type_rungs, radius_rungs, space_rungs):
    """Rewrite one file's CSS declarations. Returns (text, converted, skipped)."""
    converted = skipped = 0

    def do_font(match):
        nonlocal converted, skipped
        token = snap(int(match.group(2)), type_rungs)
        if token is None:
            skipped += 1
            return match.group(0)
        converted += 1
        return f"{match.group(1)}var(--{token})"

    def do_radius(match):
        nonlocal converted, skipped
        value_text = match.group(2)
        bang = ""
        if "!important" in value_text:
            value_text = value_text.split("!important")[0]
            bang = " !important"
        parts = value_text.split()
        # 50% is a circle, not a rung; a shorthand with a unit this scale does not carry
        # is left whole rather than half-converted.
        if not parts or not all(re.fullmatch(r"\d+px|0", p) for p in parts):
            return match.group(0)
        out, changed = [], 0
        for part in parts:
            if part == "0":
                out.append("0")
                continue
            token = snap(int(part.removesuffix("px")), radius_rungs)
            if token is None:
                skipped += 1
                return match.group(0)
            out.append(f"var(--{token})")
            changed += 1
        if not changed:
            return match.group(0)
        converted += changed
        tail = "" if bang else value_text[len(value_text.rstrip()):]
        return match.group(1) + " ".join(out) + bang + tail

    def do_spacing(match):
        nonlocal converted, skipped
        value_text = match.group(2)
        # ``!important`` is part of the declaration, not of the value. Rejecting the
        # whole declaration because of it would leave the console's overriding rules —
        # exactly the ones an adopter most needs to retheme — as literals.
        bang = ""
        if "!important" in value_text:
            value_text = value_text.split("!important")[0]
            bang = " !important"
        parts = value_text.split()
        # ``auto`` is a keyword, not a length, and passes through: ``margin:0 auto 12px``
        # still has a rung in it and should not be abandoned for the sake of the word in
        # the middle. Anything else this scale does not carry — %, calc(), em, a var()
        # already there — means the shorthand is not ours, and a half-rewrite is worse
        # than none.
        keywords = {"auto", "inherit", "initial", "unset"}
        if not parts or not all(
                p in keywords or re.fullmatch(r"-?\d+px|0", p) for p in parts):
            return match.group(0)
        out, changed = [], 0
        for part in parts:
            if part == "0" or part in keywords:
                out.append(part)              # a zero or a keyword is not a rung
                continue
            pixels = int(part.removesuffix("px"))
            token = snap(pixels, space_rungs) if pixels >= 0 else None
            if token is None:
                skipped += 1
                return match.group(0)         # a negative offset is a position
            out.append(f"var(--{token})")
            changed += 1
        if not changed:
            return match.group(0)
        converted += changed
        # The trailing whitespace the value ran up to is part of the match; put it back
        # so the declaration is spaced exactly as it was.
        tail = "" if bang else value_text[len(value_text.rstrip()):]
        return match.group(1) + " ".join(out) + bang + tail

    text = FONT_SIZE.sub(do_font, text)
    text = RADIUS.sub(do_radius, text)
    text = SPACING.sub(do_spacing, text)
    return text, converted, skipped


__all__ = ["FONT_SIZE", "RADIUS", "SPACING", "convert_text", "snap"]
