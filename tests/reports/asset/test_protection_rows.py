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

"""BRI rating and industry-group row builders in the asset protection page.

Both are row-shaping helpers: what reaches the PDF, and what is left out so
an empty block does not render as a hazard the asset does not have.
"""

from reports.asset.protection import _bri_rating_rows, _industry_group_rows


class TestBriRatingRows:
    def test_a_float_score_is_shown_to_four_places(self):
        rows = _bri_rating_rows({"BRIRating": "B", "BRIScore": 0.123456})
        assert rows == [("Overall", "B / 0.1235")]

    def test_a_non_float_score_renders_as_a_dash(self):
        """Scores arrive as None or a string from older records; the row still
        appears, because the rating alone is worth showing."""
        assert _bri_rating_rows({"BRIRating": "B", "BRIScore": None}) == [
            ("Overall", "B / —")]
        assert _bri_rating_rows({"BRIRating": "B", "BRIScore": "n/a"}) == [
            ("Overall", "B / —")]

    def test_a_score_without_a_rating_still_renders(self):
        assert _bri_rating_rows({"BRIScore": 0.5}) == [("Overall", "— / 0.5000")]

    def test_a_peril_with_neither_rating_nor_score_is_omitted(self):
        """The point of the helper: an absent peril must not appear as an
        empty row, which would read as a hazard assessed at nothing."""
        assert _bri_rating_rows({}) == []
        assert _bri_rating_rows({"BRIWindRating": None,
                                 "BRIWindScore": None}) == []

    def test_perils_keep_their_declared_order(self):
        rows = _bri_rating_rows({
            "BRISeismicRating": "C", "BRIWindRating": "A", "BRIRating": "B"})
        assert [label for label, _ in rows] == ["Overall", "Wind", "Seismic"]

    def test_a_zero_score_is_not_treated_as_absent(self):
        """0.0 is falsy but is a real assessment, not a missing one."""
        assert _bri_rating_rows({"BRIFireRating": "E", "BRIFireScore": 0.0}) == [
            ("Fire", "E / 0.0000")]


class TestIndustryGroupRows:
    def test_codes_are_joined(self):
        assert _industry_group_rows({"IndustryGroups": {"WindCodes": ["W1", "W2"]}}) == [
            ("Wind Codes", "W1, W2")]

    def test_empty_and_missing_code_lists_are_skipped(self):
        """An empty list must not render a heading with nothing under it."""
        rows = _industry_group_rows({"IndustryGroups": {
            "WindCodes": [], "FireCodes": None, "SeismicCodes": ["S1"]}})
        assert rows == [("Seismic Codes", "S1")]

    def test_a_missing_block_yields_no_rows(self):
        assert _industry_group_rows({}) == []
        assert _industry_group_rows({"IndustryGroups": None}) == []

    def test_groups_keep_their_declared_order(self):
        rows = _industry_group_rows({"IndustryGroups": {
            "SeismicCodes": ["S"], "WindCodes": ["W"], "FireCodes": ["F"]}})
        assert [label for label, _ in rows] == [
            "Wind Codes", "Fire Codes", "Seismic Codes"]
