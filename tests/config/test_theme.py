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
        rungs = [self._px(SPACE[f"space-{i}"]) for i in range(1, len(SPACE) + 1)]
        assert rungs == sorted(rungs)
        assert len(set(rungs)) == len(rungs), "two space rungs share a value"

    def test_radius_ladder_ascends(self):
        order = ["radius-xs", "radius-sm", "radius-md", "radius-lg", "radius-xl",
                 "radius-2xl"]
        rungs = [self._px(RADIUS[name]) for name in order]
        assert rungs == sorted(rungs)

    def test_type_ladder_ascends(self):
        order = ["size-3xs", "size-xxs", "size-xs", "size-sm", "size-md", "size-base",
                 "size-lg", "size-xl", "size-2xl", "size-3xl", "size-4xl"]
        rungs = [self._px(TYPE[name]) for name in order]
        assert rungs == sorted(rungs)
        assert len(set(rungs)) == len(rungs), "two type rungs share a value"

    def test_space_ladder_is_contiguous(self):
        """No gap in the numbering — ``space-7`` missing would be a silent hole."""
        assert set(SPACE) == {f"space-{i}" for i in range(1, len(SPACE) + 1)}


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
