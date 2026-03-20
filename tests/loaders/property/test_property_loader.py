# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

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

    def test_custom_filename(self, tmp_path):
        from loaders.property_loader import PropertyLoader
        write_json(tmp_path / "my_props.json", property_json(2))
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
