# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Coverage tests for the value-formatter error branches: non-numeric
percentage and coordinate inputs."""

from visual.utils.formatters._value import _ValueFormattersMixin as F


class TestValueFormatterErrorBranches:
    def test_format_percentage_non_numeric_returns_str(self):
        # float("abc") raises ValueError -> returns str(value) (lines 96-97).
        assert F.format_percentage("abc") == "abc"

    def test_format_coordinates_non_numeric_returns_na(self):
        # "x" >= 0 raises TypeError -> returns "N/A" (lines 119-120).
        assert F.format_coordinates("x", "y") == "N/A"
