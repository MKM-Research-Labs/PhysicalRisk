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

"""Tests for config.theme — the design-token vocabulary (coding rule R7).

The invariants here are the ones a rename can break silently. A duplicate token name
would let two groups define the same custom property and leave the winner to file
order; a non-string value would emit a ``:root`` declaration the browser drops. Both
fail in the browser rather than in Python, which is why they are asserted here.
"""

import re

import pytest

from config.theme import (
    BRAND, DEPTH, DEPTH_BAND_BOUNDS_M, DEPTH_BAND_TOKENS, DEPTH_BAND_TOP, FLOOD,
    FLOOD_RISK_MARKERS, FLOOD_RISK_TOKENS, HUE, LOAN_RISK_TOKENS, LTV_BAND_BOUNDS,
    LTV_BAND_TOKENS, LTV_BAND_TOP, MAP, MARKER, OPERATIONAL_STATUS_TOKENS, PERIL,
    PROPERTY_TYPE_TOKENS, RADIUS, RAG, SERIES, SHADOW, SIGN, SPACE, STATE,
    STATUS_TOKEN_RAMPS, STORM_INTENSITY_BOUNDS_MS, STORM_INTENSITY_TOKENS,
    STORM_INTENSITY_TOP, SURFACE, TEXT, THEME, THEME_GROUPS, TYPE,
)
from config.theme import (
    RAG_TOKENS, STATUS_COLOUR_DEFAULTS, STATUS_COLOUR_TOKENS,
    TRIGGER_LEVEL_BG_TOKENS, TRIGGER_LEVEL_CHART_TOKENS,
    TRIGGER_LEVEL_DARK_TOKENS, TRIGGER_LEVEL_TOKENS,
)
from config.theme.registry import SANCTIONED_PACKAGE

# A CSS custom-property name: what a token is allowed to be called, so a token can
# never be spelled in a way the emitted block cannot express.
_TOKEN_NAME = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")


class TestTokenNames:
    def test_names_are_unique_across_groups(self):
        """The groups organise the package; they do not namespace it.

        A CSS custom property has one flat namespace. Two groups defining ``--line``
        would resolve by emission order, which is a silent, order-dependent bug.
        """
        names = [name for _, group in THEME_GROUPS for name in group]
        duplicates = sorted({n for n in names if names.count(n) > 1})
        assert duplicates == [], f"token names defined in more than one group: {duplicates}"

    def test_names_are_valid_custom_properties(self):
        for name in THEME:
            assert _TOKEN_NAME.match(name), f"{name!r} is not a usable custom-property name"

    def test_theme_is_exactly_the_union_of_the_groups(self):
        union = {name: value for _, group in THEME_GROUPS for name, value in group.items()}
        assert THEME == union

    def test_every_group_is_registered(self):
        """A group added to the package but not to THEME_GROUPS is never emitted."""
        declared = {id(group) for _, group in THEME_GROUPS}
        for group in (BRAND, SURFACE, TEXT, RAG, STATE, HUE, PERIL, DEPTH, MAP,
                      MARKER, FLOOD, SIGN, SERIES, TYPE, SPACE, RADIUS, SHADOW):
            assert id(group) in declared

    def test_group_labels_are_unique(self):
        labels = [label for label, _ in THEME_GROUPS]
        assert len(labels) == len(set(labels))


class TestTokenValues:
    def test_values_are_non_empty_strings(self):
        """A non-string or blank value emits a declaration the browser drops."""
        for name, value in THEME.items():
            assert isinstance(value, str), f"--{name} is {type(value).__name__}, not str"
            assert value.strip(), f"--{name} is blank"

    def test_values_carry_no_declaration_syntax(self):
        """A stray ``;`` or ``:`` would terminate the declaration early."""
        for name, value in THEME.items():
            assert ";" not in value, f"--{name} contains a semicolon"
            assert "}" not in value, f"--{name} contains a closing brace"

    @pytest.mark.parametrize("group", [BRAND, SURFACE, TEXT, RAG, STATE, HUE,
                                       PERIL, DEPTH, MAP, MARKER, FLOOD, SIGN,
                                       SERIES])
    def test_colour_groups_hold_colours(self, group):
        for name, value in group.items():
            assert value.startswith("#") or value.startswith("rgb"), \
                f"--{name} = {value!r} is not a colour"

    @pytest.mark.parametrize("group", [SPACE, RADIUS])
    def test_length_groups_hold_lengths(self, group):
        for name, value in group.items():
            assert value.endswith("px"), f"--{name} = {value!r} is not a length"

    def test_type_sizes_are_lengths(self):
        for name, value in TYPE.items():
            if name.startswith("size-"):
                assert value.endswith("px"), f"--{name} = {value!r} is not a length"

    #: ModelRisk's ladders, which every shared name must still carry exactly.
    MODELRISK_SCALE = {
        "size-xxs": "10px", "size-xs": "11px", "size-sm": "12px", "size-md": "13px",
        "size-lg": "16px", "size-xl": "20px",
        "space-1": "2px", "space-2": "4px", "space-3": "6px", "space-4": "8px",
        "space-5": "10px", "space-6": "12px", "space-7": "14px", "space-8": "16px",
        "space-9": "18px", "space-10": "24px",
        "radius-sm": "3px", "radius-md": "6px", "radius-lg": "8px",
        "radius-xl": "10px", "radius-pill": "12px",
    }

    def test_shared_rungs_carry_modelrisk_values(self):
        """A shared name means a shared value, on the scales as on the colours."""
        wrong = {name: (want, THEME[name])
                 for name, want in self.MODELRISK_SCALE.items()
                 if THEME[name] != want}
        assert wrong == {}, f"diverged from ModelRisk: {wrong}"

    def test_our_extra_rungs_are_named_by_pixel_value(self):
        """The rungs ModelRisk's ladders lack, so their provenance is legible.

        ModelRisk stops at 20px type, has no 4px radius and no 1px hairline, because it
        does not need them. Adding those is extending the vocabulary for a need it does
        not have — the same thing the colour groups do — not diverging from it. Naming
        them by pixel value keeps a shared name from ever being one of ours.
        """
        extras = ({k for k in TYPE if k.startswith("size-")} | set(SPACE) | set(RADIUS)
                  ) - set(self.MODELRISK_SCALE)
        assert extras == {
            "size-8", "size-14", "size-18", "size-24", "size-28", "size-32", "size-36",
            "space-hair", "space-wide", "space-inset", "radius-4",
        }

    def test_shadows_are_whole_box_shadow_values(self):
        """Whole values, not the colours inside them.

        An adopter with a flatter house style sets one to ``none`` and the elevation
        goes away everywhere; that only works if the token is the whole declaration.
        """
        for name, value in SHADOW.items():
            assert "rgba(" in value or value == "none", f"--{name} = {value!r}"


class TestScales:
    """A scale is only useful if the markup can reach for it.

    MKM-ModelRisk shipped a six-rung spacing scale, found the console reached for a
    2px step, and had to correct it before anything consumed it. These hold the
    ladders monotonic so a later edit cannot quietly put a rung out of order.
    """

    @staticmethod
    def _px(value):
        return int(value.removesuffix("px"))

    def test_space_ladder_ascends(self):
        """ModelRisk's ten numbered rungs ascend; ours are named, not numbered."""
        rungs = [self._px(SPACE[f"space-{i}"]) for i in range(1, 11)]
        assert rungs == sorted(rungs)
        values = [self._px(v) for v in SPACE.values()]
        assert len(set(values)) == len(values), "two space rungs share a value"

    def test_radius_ladder_ascends(self):
        order = ["radius-sm", "radius-4", "radius-md", "radius-lg", "radius-xl",
                 "radius-pill"]
        rungs = [self._px(RADIUS[name]) for name in order]
        assert rungs == sorted(rungs)
        assert set(RADIUS) == set(order)

    def test_type_ladder_ascends(self):
        sizes = sorted((self._px(v) for k, v in TYPE.items() if k.startswith("size-")))
        assert sizes == sorted(set(sizes)), "two type rungs share a value"
        assert sizes[0] == 8 and sizes[-1] == 36

    def test_space_numbering_is_contiguous(self):
        """No gap in ModelRisk's numbering — ``space-7`` missing would be a silent hole.

        Our own rungs are named rather than numbered (``space-px``, ``space-20``,
        ``space-40``) precisely so they cannot open one.
        """
        numbered = {k for k in SPACE if k.removeprefix("space-").isdigit()}
        assert numbered == {f"space-{i}" for i in range(1, 11)}, (
            "a numeric suffix on this scale means a rung index, never a pixel value"
        )


class TestSanctionedPackage:
    def test_names_the_theme_package(self):
        """The styling audit exempts exactly this path; a typo would exempt nothing."""
        assert SANCTIONED_PACKAGE == "config/theme"

    def test_typeface_is_a_token(self):
        """The face is the first thing a rebrand changes.

        ModelRisk defined ``--font`` in its step 1 and did not reference it until step
        6, so a rebrand would have stopped at the colours. Holding it here keeps the
        omission from repeating.
        """
        assert TYPE["font"]
        assert TYPE["font-mono"]


class TestStatusRamps:
    """The value→token ramps (``config.theme._status``).

    These exist so a business value and the colour it is drawn in are decided once.
    The invariant that matters is that every ramp points at a token the palette
    actually defines — a ramp naming a token that does not exist resolves to nothing,
    and the drawing code would paint with ``None``.
    """

    def test_every_ramp_resolves_to_defined_tokens(self):
        unresolved = [
            f"{ramp}[{value!r}] -> {token}"
            for ramp, mapping in STATUS_TOKEN_RAMPS.items()
            for value, token in mapping.items()
            if token not in THEME
        ]
        assert unresolved == [], "ramps naming undefined tokens: " + ", ".join(unresolved)

    def test_every_ramp_is_registered(self):
        registered = {id(m) for m in STATUS_TOKEN_RAMPS.values()}
        for ramp in (FLOOD_RISK_TOKENS, OPERATIONAL_STATUS_TOKENS, LOAN_RISK_TOKENS,
                     PROPERTY_TYPE_TOKENS, STORM_INTENSITY_TOKENS, DEPTH_BAND_TOKENS,
                     LTV_BAND_TOKENS):
            assert id(ramp) in registered

    def test_lookup_ramps_carry_an_unknown_band(self):
        """A ramp keyed on free-text data needs a landing place for a value it
        has never seen. The banded ramps (storm, depth, LTV) are keyed on a number
        and cannot miss, so they are excluded."""
        for ramp in (FLOOD_RISK_TOKENS, OPERATIONAL_STATUS_TOKENS, LOAN_RISK_TOKENS,
                     PROPERTY_TYPE_TOKENS):
            assert "Unknown" in ramp

    def test_marker_ramp_holds_folium_names_not_tokens(self):
        """Leaflet markers take a name from a fixed vocabulary, not a colour.

        If one of these were ever changed to a token name like ``red-deep`` it would
        silently stop being a valid marker colour and the marker would fall back to
        blue on the map. Membership of Folium's vocabulary is the check; some names
        (``green``, ``purple``) are also token names, which is a coincidence of
        spelling and not a problem.
        """
        folium_names = {"red", "darkred", "lightred", "orange", "beige", "green",
                        "darkgreen", "lightgreen", "blue", "darkblue", "cadetblue",
                        "lightblue", "purple", "darkpurple", "pink", "white",
                        "gray", "lightgray", "black"}
        for value, name in FLOOD_RISK_MARKERS.items():
            assert name in folium_names, f"{value!r} -> {name!r} is not a Folium colour"

    def test_marker_ramp_covers_the_token_ramp(self):
        """Every band with a colour has a marker, so a map and a popup agree."""
        assert set(FLOOD_RISK_TOKENS) <= set(FLOOD_RISK_MARKERS)

    def test_both_casings_of_each_flood_band_agree(self):
        """The data carries both casings; they must not drift to different colours."""
        for lower, upper in (("Very low", "Very Low"), ("Very high", "Very High")):
            assert FLOOD_RISK_TOKENS[lower] == FLOOD_RISK_TOKENS[upper]
            assert FLOOD_RISK_MARKERS[lower] == FLOOD_RISK_MARKERS[upper]


class TestBandBounds:
    """The thresholds the numeric ramps are cut at."""

    @pytest.mark.parametrize("bounds,ramp", [
        (STORM_INTENSITY_BOUNDS_MS, STORM_INTENSITY_TOKENS),
        (DEPTH_BAND_BOUNDS_M, DEPTH_BAND_TOKENS),
        (LTV_BAND_BOUNDS, LTV_BAND_TOKENS),
    ])
    def test_bounds_ascend(self, bounds, ramp):
        values = [bound for bound, _ in bounds]
        assert values == sorted(values)

    @pytest.mark.parametrize("bounds,ramp,top", [
        (STORM_INTENSITY_BOUNDS_MS, STORM_INTENSITY_TOKENS, STORM_INTENSITY_TOP),
        (DEPTH_BAND_BOUNDS_M, DEPTH_BAND_TOKENS, DEPTH_BAND_TOP),
        (LTV_BAND_BOUNDS, LTV_BAND_TOKENS, LTV_BAND_TOP),
    ])
    def test_every_band_named_by_the_bounds_has_a_colour(self, bounds, ramp, top):
        for _, band in bounds:
            assert band in ramp, f"band {band!r} has no colour"
        assert top in ramp, f"top band {top!r} has no colour"

    @pytest.mark.parametrize("bounds,ramp,top", [
        (STORM_INTENSITY_BOUNDS_MS, STORM_INTENSITY_TOKENS, STORM_INTENSITY_TOP),
        (DEPTH_BAND_BOUNDS_M, DEPTH_BAND_TOKENS, DEPTH_BAND_TOP),
        (LTV_BAND_BOUNDS, LTV_BAND_TOKENS, LTV_BAND_TOP),
    ])
    def test_no_band_is_unreachable(self, bounds, ramp, top):
        """A colour in the ramp that no bound selects would never be drawn."""
        reachable = {band for _, band in bounds} | {top}
        assert set(ramp) == reachable, f"unreachable bands: {set(ramp) - reachable}"


class TestBadgeRamps:
    """The console's own workflow-state ramps (``config.theme._badges``).

    These replaced 22 object literals in ``src/static/js``. The reason they are worth
    testing separately from the domain ramps is that the front end reaches them through
    a name — ``Theme.ramp('rag_rating')`` — so a renamed ramp fails at the browser,
    silently, on whichever panel nobody opened.
    """

    def test_every_ramp_resolves_to_defined_tokens(self):
        unresolved = [
            f"{ramp}[{value!r}] -> {token}"
            for ramp, mapping in STATUS_COLOUR_TOKENS.items()
            for value, token in mapping.items()
            if token not in THEME
        ]
        assert unresolved == [], "ramps naming undefined tokens: " + ", ".join(unresolved)

    def test_every_default_is_a_real_token(self):
        bad = {r: t for r, t in STATUS_COLOUR_DEFAULTS.items() if t not in THEME}
        assert bad == {}

    def test_defaults_only_name_ramps_that_exist(self):
        """A default for a ramp that is gone is dead configuration."""
        orphans = sorted(set(STATUS_COLOUR_DEFAULTS) - set(STATUS_COLOUR_TOKENS))
        assert orphans == []

    def test_the_three_families_share_one_flat_namespace(self):
        """The front end asks for a ramp by name and cannot see which module it is in.

        Two families defining the same ramp name would resolve by merge order, which is
        a silent, order-dependent bug — the same failure mode as a duplicate token.
        """
        from config.theme import (
            BADGE_TOKEN_RAMPS, GOVERNANCE_TOKEN_RAMPS, STATUS_TOKEN_RAMPS,
        )
        names = (list(STATUS_TOKEN_RAMPS) + list(GOVERNANCE_TOKEN_RAMPS)
                 + list(BADGE_TOKEN_RAMPS))
        duplicates = sorted({n for n in names if names.count(n) > 1})
        assert duplicates == []
        assert len(STATUS_COLOUR_TOKENS) == len(names)

    def test_ramp_names_are_javascript_safe(self):
        """A ramp is addressed by name from JS; keep them plain identifiers."""
        for name in STATUS_COLOUR_TOKENS:
            assert re.match(r"^[a-z][a-z0-9_]*$", name), name


class TestTriggerLevels:
    """The ramp that existed five times in four different spellings.

    Collapsing it is the one place this migration deliberately changes what is on
    screen, so the shape of the result is pinned rather than left implicit.
    """

    LEVELS = ("alert", "warning", "severe", "clean")

    def test_all_forms_cover_the_same_levels(self):
        """A level with a foreground but no background would draw ink on nothing."""
        for form in (TRIGGER_LEVEL_TOKENS, TRIGGER_LEVEL_DARK_TOKENS,
                     TRIGGER_LEVEL_BG_TOKENS, TRIGGER_LEVEL_CHART_TOKENS):
            assert set(form) == set(self.LEVELS)

    def test_the_chart_form_is_brighter_than_the_badge_form(self):
        """They are deliberately different; if they converge, one of them is wrong."""
        for level in ("alert", "warning", "severe"):
            assert TRIGGER_LEVEL_CHART_TOKENS[level] != TRIGGER_LEVEL_TOKENS[level]

    def test_the_three_forms_are_distinct_per_level(self):
        """A tint that equals its ink is an invisible badge."""
        for level in self.LEVELS:
            fg = THEME[TRIGGER_LEVEL_TOKENS[level]]
            bg = THEME[TRIGGER_LEVEL_BG_TOKENS[level]]
            assert fg != bg, f"{level}: foreground and background are the same colour"

    def test_alert_is_no_longer_the_accent_blue(self):
        """sp_table_basis drew "alert" in the accent, which made the same word mean
        caution on one screen and information on another. That is the visible change
        step 3 set out to make."""
        assert TRIGGER_LEVEL_TOKENS["alert"] != "accent"

    def test_severity_deepens_from_alert_to_severe(self):
        """The ladder must not be reordered into an incoherent ramp."""
        assert TRIGGER_LEVEL_TOKENS["alert"] == "gold-bright"
        assert TRIGGER_LEVEL_TOKENS["warning"] == "amber"
        assert TRIGGER_LEVEL_TOKENS["severe"] == "red"


class TestRagVocabulary:
    """RAG means the same thing wherever it is drawn."""

    def test_rag_ramp_uses_the_rag_palette(self):
        for value, token in RAG_TOKENS.items():
            if value != "Not Rated":
                assert THEME[token] in THEME.values()
                assert token.split("-")[0] in {"green", "amber", "red"}, token


class TestModelRiskVocabulary:
    """A token name means the same thing in PhysicalRisk and MKM-ModelRisk.

    The two products are meant to sit in one suite and ModelRisk was extracted from this
    codebase, so a single adopter theme file should brand both. That only works if a
    shared name carries a shared value: an institution setting ``--green`` for its house
    palette must not get one green in the console and a different one in the governance
    platform.

    The values below are ModelRisk's, asserted here rather than imported because the two
    repositories are separate checkouts and a test may not have the other one on disk.
    Reconciled 2026-08-28 against ModelRisk's ``config/theme.py``; 33 names collided and
    13 of them were colours, all resolved in ModelRisk's favour.
    """

    #: Names the two products share, with the value both must carry.
    MODELRISK_VALUES = {
        "accent": "#1976d2", "accent-soft": "#e3f2fd", "accent-border": "#bbdefb",
        "accent-ink": "#0d47a1", "accent-wash": "#f7fbff", "header-from": "#f5f7fa",
        "header-to": "#c3cfe2", "header-ink": "#2a3a4d", "header-sub": "#5b6b7d",
        "bg": "#eef1f5", "panel": "#ffffff", "raised": "#fafafa", "sunken": "#f5f5f5",
        "control": "#f9f9f9", "readonly": "#f4f5f7", "code": "#f0f0f0",
        "line": "#e0e0e0", "line-soft": "#eeeeee",
        "text": "#333333", "text-2": "#555555", "muted": "#888888",
        "inverse": "#ffffff",
        "green": "#388e3c", "amber": "#f57c00", "red": "#d32f2f", "grey": "#9e9e9e",
        "green-soft": "#66bb6a", "amber-soft": "#ffa726", "red-soft": "#ef5350",
        "danger-bg": "#fdecea", "danger-ink": "#b71c1c", "danger-line": "#f5c6c2",
        "danger-line-soft": "#f1c5c2", "warn-bg": "#fff8e1", "warn-bg-alt": "#fef3c7",
        "warn-ink": "#92400e", "warn-line": "#d97706", "warn-ink-alt": "#b26a00",
        "ok-bg": "#e8f5e9",
        "info": "#0288d1", "violet": "#8e24aa", "blue-grey": "#607d8b",
        "gold": "#b8860b", "slate": "#94a3b8", "teal": "#00897b",
    }

    def test_shared_names_carry_the_shared_value(self):
        wrong = {
            name: (expected, THEME[name])
            for name, expected in self.MODELRISK_VALUES.items()
            if name in THEME and THEME[name].lower() != expected.lower()
        }
        assert wrong == {}, f"diverged from ModelRisk: {wrong}"

    def test_no_shared_name_has_been_dropped(self):
        missing = sorted(n for n in self.MODELRISK_VALUES if n not in THEME)
        assert missing == [], f"tokens ModelRisk defines that we no longer do: {missing}"

    def test_our_darker_tones_kept_names_of_their_own(self):
        """The values ModelRisk does not have are still available, under new names.

        ``green``/``red``/``gold``/``accent-ink`` moved to ModelRisk's values; the tones
        they used to carry are what the map markers and PDF palettes draw with, so they
        had to survive the rename rather than be dropped.
        """
        assert THEME["green-dark"] == "#2e7d32"
        assert THEME["red-dark"] == "#c62828"
        assert THEME["gold-bright"] == "#fbc02d"
        assert THEME["accent-mid"] == "#1565c0"
