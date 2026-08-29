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

"""The CDM Asset Review tool's own surface palette.

``tools/cdm_property_editor`` is a separate application on its own port, and it was
built with a cooler, bluer identity than the console: pale blue washes where the console
uses neutral greys, and blue-grey borders where the console uses plain ones. That is a
legitimate difference — it is a different product surface, the same way the map markers
are — so it gets its own group rather than being flattened into the shared palette or
flattening the shared palette into it.

Every value here is what the tool draws today, exactly. Of the 65 distinct colours in its
838-line stylesheet, 38 turned out to be within 1.5 ΔE of a token the shared palette
already had and now use it; these 27 are the remainder, and they are the tool's identity.

**This group has known drift.** ``rv-line`` and ``rv-line-2`` are 0.5 ΔE apart, as are
``rv-border`` and ``rv-border-2``; the pale-wash rungs sit within 2 ΔE of one another.
A design pass should collapse the cool-neutral ramp to four or five rungs. That pass is
not this migration: collapsing them changes what the tool looks like, and it is a tool
someone uses. Recorded here so the decision is available rather than buried in 838 lines
of stylesheet.

The ``rv-`` prefix keeps them out of the shared vocabulary, so an adopter theming both
products does not have to reason about a tool they may not deploy.
"""

# --- The cool neutral ramp: borders and dividers, dark to light. -----------------
REVIEW = {
    "rv-ink": "#45506a",
    "rv-ink-2": "#444444",
    "rv-ink-3": "#445555",
    "rv-sub": "#607080",
    "rv-muted": "#aab2bf",
    "rv-border": "#b3bcc8",
    "rv-border-2": "#b9c4d4",
    "rv-line": "#c3ccd8",
    "rv-line-2": "#d6dbe4",
    "rv-line-3": "#d7dde6",
    "rv-divider": "#dfe6ef",
    "rv-divider-2": "#e0e5ec",
    "rv-rule": "#e3e7ee",
    "rv-rule-2": "#e3e8ef",

    # --- The pale blue washes: panel and row backgrounds. ------------------------
    "rv-wash": "#e8f0fe",
    "rv-wash-2": "#e8f1fc",
    "rv-wash-3": "#eef6ff",
    "rv-wash-4": "#f2f6fc",
    "rv-tint": "#cfe2fb",

    # --- Status accents. The tool draws its own greens and reds, muted against the
    # console's, because they sit as thin rings and inline chips on pale backgrounds
    # where the RAG tones read as heavy.
    "rv-accent": "#1967d2",
    "rv-ok": "#2c7a2c",
    "rv-ok-line": "#9cc79e",
    "rv-ok-ring": "#cfe6d0",
    "rv-bad": "#b03030",
    "rv-bad-line": "#d9b3b3",
    "rv-bad-bg": "#fdf3f3",
    "rv-crimson": "#c2185b",

    # --- Elevation and overlays. ``0 8px 32px rgba(0, 0, 0, 0.3)`` is not here: it is
    # exactly the shared ``shadow-modal``, and the tool's two modals use that. These are
    # the values with no shared equivalent. The two white veils the tool drew at 0.70 and
    # 0.72 alpha are collapsed to one — a 0.02 difference on a white overlay is below
    # what a display can resolve, so this is the one consolidation made here rather than
    # deferred to a design pass.
    "rv-shadow-card": "0 1px 2px rgba(0, 0, 0, 0.03)",
    "rv-shadow-chip": "0 1px 3px rgba(0, 0, 0, 0.4)",
    "rv-shadow-panel": "0 4px 16px rgba(0, 0, 0, 0.18)",
    "rv-scrim": "rgba(0, 0, 0, 0.25)",
    "rv-scrim-deep": "rgba(0, 0, 0, 0.35)",
    "rv-veil": "rgba(255, 255, 255, 0.7)",
    "rv-veil-strong": "rgba(255, 255, 255, 0.9)",
}

__all__ = ["REVIEW"]
