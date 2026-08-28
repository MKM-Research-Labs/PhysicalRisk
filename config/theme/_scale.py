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

"""The non-colour visual parameters: type, spacing, corner radius and elevation.

The other half of rule R7, and the half that is easier to get wrong. A scale is only
useful if the markup can actually reach for it: MKM-ModelRisk shipped a six-rung
spacing scale, found the console reached for a 2px step, and had to correct it before
anything consumed it. These ladders are therefore measured from the source rather
than chosen — the counts in each comment are the live histogram over
``src/static`` and ``tools`` at 2026-08-28.

Rungs the code reaches for fewer than about ten times are deliberately absent. They
are genuine one-offs, and giving each a token would relocate the noise rather than
remove it; they stay literals and the audit's backlog count keeps them visible.
"""

# The body face, and the two spellings the console has drifted into: 21 sites say
# "Arial, sans-serif", four say "Arial, Helvetica, sans-serif", and the monospace
# stack is spelled two ways as well (34 bare ``monospace``, four with a real ramp).
# One stack each, so an adopter's face and its fallbacks arrive together. The face is
# the first thing a rebrand changes, so it is a token from the outset rather than the
# literal that a colours-only conversion would leave behind.
TYPE = {
    "font": "Arial, Helvetica, sans-serif",
    "font-mono": "ui-monospace, SFMono-Regular, Menlo, monospace",
    "line-height": "1.5",
    # 8px×13, 9px×77, 10px×376, 11px×391, 12px×159, 13px×72, 14px×40, 16px×25,
    # 18px×22, 20px×7, 24px×17. A 1px step from 8 to 14 is not a designer's ladder,
    # it is what a dense analytics console converges on; 15, 22, 28, 32 and 36 are
    # each used a handful of times and are left off-scale.
    "size-3xs": "8px",
    "size-xxs": "9px",
    "size-xs": "10px",
    "size-sm": "11px",
    "size-md": "12px",
    "size-base": "13px",
    "size-lg": "14px",
    "size-xl": "16px",
    "size-2xl": "18px",
    "size-3xl": "20px",
    "size-4xl": "24px",
}

# A 1px step at the low end, widening above 12px — 8px×327, 6px×284, 4px×269,
# 2px×189, 12px×146, 3px×137, 5px×133, 16px×114, 10px×100, 40px×84, 1px×45, 20px×44,
# 14px×21, 24px×17. The rung number is a position on the ladder, not a pixel count;
# the value is the authority. An adopter tightens or loosens the whole interface by
# editing these.
SPACE = {
    "space-1": "1px",
    "space-2": "2px",
    "space-3": "3px",
    "space-4": "4px",
    "space-5": "5px",
    "space-6": "6px",
    "space-7": "8px",
    "space-8": "10px",
    "space-9": "12px",
    "space-10": "14px",
    "space-11": "16px",
    "space-12": "20px",
    "space-13": "24px",
    # The panel inset the docked side panels share.
    "space-14": "40px",
}

# 4px×172, 3px×84, 8px×61, 6px×57, 10px×17, 2px×12. 1, 5, 9 and 12 are one-offs.
RADIUS = {
    "radius-xs": "2px",
    "radius-sm": "3px",
    "radius-md": "4px",
    "radius-lg": "6px",
    "radius-xl": "8px",
    "radius-2xl": "10px",
    "radius-pill": "999px",
}

# Whole ``box-shadow`` values rather than the colours inside them, so an adopter with
# a flatter house style sets one to ``none`` and the elevation goes away everywhere.
# The console's modals currently carry four near-identical spellings of one shadow
# (``0 8px 32px`` at 0.2, 0.25 and 0.3 alpha, plus ``0 4px 20px`` at 0.3); they are
# recorded as two tokens rather than four, because the difference is invisible and
# these are the one place in this file where near-duplicates cost nothing to merge.
SHADOW = {
    "shadow-card": "0 1px 3px rgba(0, 0, 0, 0.15)",
    "shadow-panel": "0 2px 8px rgba(0, 0, 0, 0.15)",
    "shadow-float": "0 4px 20px rgba(0, 0, 0, 0.3)",
    "shadow-modal": "0 8px 32px rgba(0, 0, 0, 0.3)",
}

__all__ = ["TYPE", "SPACE", "RADIUS", "SHADOW"]
