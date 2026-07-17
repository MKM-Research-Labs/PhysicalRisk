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

"""Tests for PropertyLoader."""

from tests.loaders.conftest import property_json, write_json


class TestPropertyLoaderBasic:

    def test_load_all_returns_list(self, tmp_path):
        from loaders.property_loader import PropertyLoader
        write_json(tmp_path / "property.json", property_json(3))
        assert len(PropertyLoader(tmp_path).load_all()) == 3

    def test_missing_file_empty(self, tmp_path):
        from loaders.property_loader import PropertyLoader
        assert PropertyLoader(tmp_path).load_all() == []

    def test_custom_filename_ignored_reads_via_seam(self, tmp_path):
        # PropertyLoader reads the property portfolio through the seam now; the
        # filename arg is retained for back-compat but no longer selects the source.
        from loaders.property_loader import PropertyLoader
        write_json(tmp_path / "property.json", property_json(2))  # seeds the seam
        assert PropertyLoader(tmp_path, filename="my_props.json").count() == 2


class TestPropertyLoaderLookup:

    def test_find_by_id(self, tmp_path):
        from loaders.property_loader import PropertyLoader
        write_json(tmp_path / "property.json", property_json(3))
        assert PropertyLoader(tmp_path).find_by_id("PROP-001") is not None

    def test_list_all_has_property_id(self, tmp_path):
        from loaders.property_loader import PropertyLoader
        write_json(tmp_path / "property.json", property_json(2))
        summaries = PropertyLoader(tmp_path).list_all()
        assert "propertyId" in summaries[0]
