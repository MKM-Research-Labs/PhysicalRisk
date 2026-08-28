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
    BRAND, DEPTH, HUE, MAP, PERIL, RADIUS, RAG, SERIES, SHADOW, SIGN, SPACE,
    STATE, SURFACE, TEXT, THEME, THEME_GROUPS, TYPE,
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
                      SIGN, SERIES, TYPE, SPACE, RADIUS, SHADOW):
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
                                       PERIL, DEPTH, MAP, SIGN, SERIES])
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
