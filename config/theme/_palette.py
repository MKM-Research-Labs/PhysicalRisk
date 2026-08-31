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

"""The colour vocabulary: every hue the platform draws with, named once.

This is the colour half of coding rule R7 — the console, the generated PDFs and the
map layers all resolve a *token* from here rather than writing a value down. The
scales (type, spacing, radius, shadow) live in :mod:`config.theme._scale`; the
domain ramps that map a business value to a colour live in
:mod:`config.theme._domain`.

Token names are the CSS custom-property name without the leading ``--``, so a token
is spelled identically here, in the emitted ``:root`` block, in the JavaScript and in
an adopter's override file. There is no translation layer to drift.

Names are shared with MKM-ModelRisk's ``config/theme.py`` wherever the two platforms
mean the same thing (``accent``, ``panel``, ``muted``, ``line``, the RAG hues). The
two products are meant to sit in one suite, and a single vocabulary is what lets one
adopter theme file brand both.

Values are strings, deliberately: a token is whatever CSS accepts in that position.
Nothing here is arithmetic, so nothing here needs to be a number.

The values are those the code already draws with, at the frequencies recorded in
docs/refactor/theme_centralisation_plan.md §2 — near-duplicates are named distinctly
rather than collapsed, because collapsing them moves pixels and this step is meant to
be invisible. Which of them are genuine distinctions and which are drift is settled
as each surface converts, not here.
"""

# --- The adopter's identity: the one group a rebrand almost always touches. -------
# ``accent`` is the interactive colour — links, active tabs, primary buttons, the
# selected state of anything. ``accent-ink`` is the darker blue the console reaches
# for on panel headers and hover states; it is the same decision as ``accent`` in
# nine sites out of ten and the two have already drifted apart (255 uses against
# 151), so which is which gets decided per surface as that surface converts.
BRAND = {
    "accent": "#1976d2",
    "accent-mid": "#1565c0",
    "accent-ink": "#0d47a1",
    "accent-bright": "#2196f3",
    "accent-light": "#42a5f5",
    "accent-soft": "#e3f2fd",
    "accent-border": "#bbdefb",
    "accent-pale": "#90caf9",
    "accent-wash": "#f7fbff",
    "header-from": "#f5f7fa",
    "header-to": "#c3cfe2",
    "header-ink": "#2a3a4d",
    "header-sub": "#5b6b7d",
}

# --- Paper: the neutral surfaces everything else sits on. ------------------------
# Eleven of them, which is more than a design system would choose and exactly what
# the console currently uses. ``code`` and ``line-soft`` share no value by accident:
# ``#f0f0f0`` is a fill in six sites and a hairline in the rest, and separating the
# two roles is what lets an adopter darken one without darkening the other.
SURFACE = {
    "bg": "#eef1f5",
    "panel": "#ffffff",
    "raised": "#fafafa",
    "sunken": "#f5f5f5",
    "control": "#f9f9f9",
    "readonly": "#f4f5f7",
    "wash": "#f8f9fa",
    "wash-cool": "#f8fafc",
    "code": "#f0f0f0",
    "line": "#e0e0e0",
    "line-soft": "#eeeeee",
    "line-strong": "#dddddd",
    "divider": "#cccccc",
    # A hairline over an unknown background, so it darkens whatever it crosses
    # instead of assuming the panel colour.
    "rule": "rgba(0, 0, 0, 0.12)",
    "veil": "rgba(255, 255, 255, 0.85)",
    "scrim-cool": "rgba(15, 23, 42, 0.55)",
}

# --- Ink. Six weights, and the console spells all six: 226 uses of ``muted`` -----
# against 196 of ``text`` and 195 of ``text-3``. A three-weight ramp would have
# forced half the sites to keep a literal.
TEXT = {
    "text": "#333333",
    "text-2": "#555555",
    "text-3": "#666666",
    "muted": "#888888",
    "muted-2": "#999999",
    "disabled": "#aaaaaa",
    "text-4": "#777777",
    "faint": "#bbbbbb",
    "inverse": "#ffffff",
    "black": "#000000",
}

# --- Red / Amber / Green is this platform's risk vocabulary, not a colour choice. -
# Named for the rating, not for a semantic role, because that is what they mean:
# a flood-risk band, a model's RAG rating and a gauge trigger level all draw from
# here. Four reds and four ambers are in use today; they are all recorded so the
# conversion can see them, and step 6 decides which distinctions are real.
RAG = {
    "green": "#388e3c",
    "green-dark": "#2e7d32",
    "green-bright": "#4caf50",
    "green-deep": "#1b5e20",
    "green-soft": "#66bb6a",
    "green-pale": "#a5d6a7",
    "amber": "#f57c00",
    "amber-deep": "#e65100",
    "amber-dark": "#ef6c00",
    "amber-bright": "#ff9800",
    "amber-yellow": "#ffc107",
    "amber-soft": "#ffa726",
    "amber-mid": "#ffb74d",
    "red": "#d32f2f",
    "red-dark": "#c62828",
    "red-bright": "#f44336",
    "red-deep": "#b71c1c",
    "red-alt": "#e53935",
    "red-soft": "#ef5350",
    "red-pale": "#ff8a80",
    "grey": "#9e9e9e",
}

# --- Banner and chip tints, keyed to the state they announce. ---------------------
STATE = {
    "ok-bg": "#e8f5e9",
    "warn-bg": "#fff8e1",
    "warn-bg-alt": "#fef3c7",
    "warn-bg-warm": "#fff3e0",
    "warn-ink": "#92400e",
    "warn-ink-alt": "#b26a00",
    "warn-line": "#d97706",
    "warn-line-soft": "#ffe082",
    "warn-ink-deep": "#8a6d00",
    "danger-bg": "#fdecea",
    "danger-bg-soft": "#ffebee",
    "danger-ink": "#b71c1c",
    "danger-line": "#f5c6c2",
    "danger-line-soft": "#f1c5c2",
    "danger-line-alt": "#ffcdd2",
    "danger-line-mid": "#ef9a9a",
    "danger-bg-pale": "#fff8f8",
    "ok-line": "#c8e6c9",
    "warn-line-pale": "#ffe0b2",
    "warn-line-pale-2": "#ffcc80",
    "info-bg": "#e8eaf6",
}

# --- Hues that distinguish a state without asserting a risk rating. ---------------
# Deliberately outside RAG: a peril being seismic rather than flood, or a gauge being
# the third one on a chart, is not a rating, and drawing it in a rating colour would
# read as one.
HUE = {
    "navy": "#1a237e",
    "navy-mid": "#283593",
    "navy-pale": "#c5cae9",
    "slate": "#94a3b8",
    "slate-dark": "#37474f",
    "blue-grey": "#607d8b",
    "blue-grey-dark": "#546e7a",
    "blue-grey-light": "#78909c",
    "blue-grey-pale": "#90a4ae",
    "blue-grey-bg": "#eceff1",
    "steel": "#6b7686",
    "purple": "#7b1fa2",
    "purple-deep": "#6a1b9a",
    "purple-dark": "#4a148c",
    "purple-bg": "#f3e5f5",
    "orange-deep": "#bf360c",
    "gold": "#b8860b",
    "gold-bright": "#fbc02d",
    "gold-deep": "#f9a825",
    "gold-dark": "#f57f17",
    "purple-bright": "#9c27b0",
    "purple-soft": "#ab47bc",
    "purple-pale": "#d1c4e9",
    "yellow": "#ffeb3b",
    "teal": "#00897b",
    "teal-bright": "#009688",
    "teal-mid": "#26a69a",
    "cyan-bright": "#00bcd4",
    "info": "#0288d1",
    "violet": "#8e24aa",
    "pink": "#e91e63",
    "pink-bg": "#fce4ec",
    "brown": "#795548",
    "orange-bright": "#ff5722",
    "grey-dark": "#616161",
}

# --- The admin console's dark surface. --------------------------------------------
# ``src/static/admin/admin.html`` is a standalone dark page — the only dark surface in
# the platform — served straight from disk by ``routes.admin``. Its palette has no
# overlap with the light one, so it is named separately rather than being forced through
# tokens that mean "paper" and "ink" on every other screen.
#
# It reused four names the light palette also uses (``bg``, ``panel``, ``line``,
# ``muted``) with dark values, in its own ``:root``. That worked only because the page is
# a separate document; the ``dk-`` prefix makes the separation explicit rather than
# accidental, so the two can never be served into the same document and collide.
DARK = {
    "dk-bg": "#0f1720",
    "dk-panel": "#16212e",
    "dk-line": "#27384a",
    "dk-text": "#dbe5ef",
    "dk-muted": "#8aa0b5",
    "dk-accent": "#3b9dd6",
    "dk-ok": "#2faa6a",
    "dk-bad": "#d9534f",
}

__all__ = ["BRAND", "SURFACE", "TEXT", "RAG", "STATE", "HUE", "DARK"]
