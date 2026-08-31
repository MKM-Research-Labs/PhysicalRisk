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

These ladders are **MKM-ModelRisk's**, value for value. The two products are meant to
sit in one suite and a shared token name has to carry a shared value, or a single
adopter theme file cannot brand both — an institution setting ``--radius-md`` for its
house style must not get 6px in the governance platform and 4px in the console.

That is a change of direction, recorded honestly. An earlier pass measured these from
PhysicalRisk's own frequency histogram, which gave a 1px step at the low end: the
console reaches for 10px and 11px type 767 times between them, and for 1px, 3px, 5px
and 7px spacing. ModelRisk's ladder has none of those rungs. Measuring produced a scale
that fitted every existing site, but fitting every existing site is what a catalogue
does, not what a design system does — a system is useful because it *constrains*, and
the rungs it omits are the ones it is telling you not to use.

The consequence is real and belongs in the open: the roughly 200 sites drawing a 4px
radius, and the spacing sites on 1, 3, 5, 7, 20 and 40px, have no exact rung here. They
snap to the nearest one in step 7 of docs/refactor/theme_centralisation_plan.md, which
makes that step a deliberate design change rather than the mechanical sweep it was
planned as. Nothing consumed these tokens when they were replaced, so the change costs
nothing today; it is spent in step 7.
"""

# The body face and the monospace stack, matching ModelRisk exactly. The console has
# drifted into three spellings of the body face and two of the mono stack; step 7
# collapses them onto these.
TYPE = {
    "font": "Arial, Helvetica, sans-serif",
    "font-mono": "ui-monospace, Menlo, monospace",
    "line-height": "1.5",
    # ModelRisk's six rungs, at ModelRisk's values.
    "size-xxs": "10px",
    "size-xs": "11px",
    "size-sm": "12px",
    "size-md": "13px",
    "size-lg": "16px",
    "size-xl": "20px",
    # Rungs ModelRisk's ladder does not have, named by pixel value so their provenance
    # is obvious at every call site: these are ours, and a shared name is never one of
    # them. ModelRisk stops at 20px because it has no page headings; this console has
    # them at 24, 28, 32 and 36, and snapping a 36px heading to 20px would not be
    # discipline, it would be a redesign nobody asked for.
    "size-8": "8px",
    "size-14": "14px",
    "size-18": "18px",
    "size-24": "24px",
    "size-28": "28px",
    "size-32": "32px",
    "size-36": "36px",
}

# A 2px step to 12px, then widening. Six rungs where PhysicalRisk's markup currently
# uses fifteen; the missing ones are the point, not an oversight.
SPACE = {
    # ModelRisk's ten rungs, at ModelRisk's values: a 2px step to 18px, then 24.
    "space-1": "2px",
    "space-2": "4px",
    "space-3": "6px",
    "space-4": "8px",
    "space-5": "10px",
    "space-6": "12px",
    "space-7": "14px",
    "space-8": "16px",
    "space-9": "18px",
    "space-10": "24px",
    # Ours, named rather than numbered. A numeric suffix would be ambiguous on this
    # scale in a way it is not on the others: ModelRisk's ``space-10`` is the tenth rung
    # and measures 24px, so a ``space-20`` reads as either the twentieth rung or 20px,
    # and it cannot be both. ``space-hair`` is the 1px rule used in 45 places — the one
    # value here that is not really a space; doubling it to reach ModelRisk's smallest
    # rung would thicken every hairline in the console.
    "space-hair": "1px",
    "space-wide": "20px",
    "space-inset": "40px",
}

# No 4px rung, which is PhysicalRisk's most common radius at 172 sites. They snap to
# 3px or 6px in step 7 — the single largest visible consequence of adopting this scale.
RADIUS = {
    # ModelRisk's five rungs, at ModelRisk's values.
    "radius-sm": "3px",
    "radius-md": "6px",
    "radius-lg": "8px",
    "radius-xl": "10px",
    "radius-pill": "12px",
    # Ours. 4px is this console's most common radius by a wide margin — 172 sites
    # against 3px's 84 — so it is a real rung of this product's scale, not a near-miss
    # of ModelRisk's. Rounding the dominant value to a less common neighbour would be
    # the tail wagging the dog.
    "radius-4": "4px",
}

# Whole ``box-shadow`` values rather than the colours inside them, so an adopter with a
# flatter house style sets one to ``none`` and the elevation goes away everywhere.
SHADOW = {
    "shadow-card": "0 1px 3px rgba(0, 0, 0, 0.04)",
    "shadow-card-hover": "0 1px 4px rgba(0, 0, 0, 0.12)",
    "shadow-modal": "0 8px 32px rgba(0, 0, 0, 0.3)",
    "shadow-toast": "0 4px 16px rgba(0, 0, 0, 0.25)",
    "shadow-ghost": "0 2px 8px rgba(0, 0, 0, 0.18)",
    "scrim": "rgba(0, 0, 0, 0.45)",
}

# ModelRisk's node-graph palette, carried across whole so the lineage and chain diagrams
# in the two products can be drawn from one vocabulary. Nothing in PhysicalRisk consumes
# it yet; it is here so that when the lineage panels are restyled they reach for these
# rather than inventing a parallel set.
GRAPH = {
    "indigo": "#6366f1",
    "indigo-ink": "#4338ca",
    "indigo-bg": "#eef2ff",
    "indigo-wash": "#f5f6ff",
    "teal-bg": "#e0f2f1",
    "node-ink": "#1f2937",
    "node-sub": "#4b5563",
    "node-retired": "#bbbbbb",
    "tray-bg": "#fbfcfe",
    "toast-bg": "#323232",
    "product": "#5e35b1",
    "product-bg": "#ede7f6",
    "product-ink": "#4527a0",
    "product-edge": "#7e57c2",
}

__all__ = ["TYPE", "SPACE", "RADIUS", "SHADOW", "GRAPH"]
