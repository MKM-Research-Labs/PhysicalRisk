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

"""Tests for RLoanLoader."""

import json
from tests.loaders.conftest import mortgage_json, write_json


class TestRLoanLoaderBasic:

    def test_load_all_returns_list(self, tmp_path):
        from loaders.rloan_loader import RLoanLoader
        write_json(tmp_path / "loan.json", mortgage_json(3))
        assert len(RLoanLoader(tmp_path).load_all()) == 3

    def test_list_all_returns_summaries(self, tmp_path):
        from loaders.rloan_loader import RLoanLoader
        write_json(tmp_path / "loan.json", mortgage_json(2))
        assert len(RLoanLoader(tmp_path).list_all()) == 2


class TestRLoanLoaderLookup:

    def test_find_by_id(self, tmp_path):
        from loaders.rloan_loader import RLoanLoader
        write_json(tmp_path / "loan.json", mortgage_json(3))
        assert RLoanLoader(tmp_path).find_by_id("RLOAN-001") is not None

    def test_missing_returns_none(self, tmp_path):
        from loaders.rloan_loader import RLoanLoader
        write_json(tmp_path / "loan.json", mortgage_json(2))
        assert RLoanLoader(tmp_path).find_by_id("RLOAN-999") is None

    def test_find_by_property_nested_structure(self, tmp_path):
        """find_by_property_id matches the nested RLoan.Header.PropertyID."""
        from loaders.rloan_loader import RLoanLoader
        data = {
            "loans": [
                {"RLoan": {"Header": {"RLoanID": "RLOAN-001",
                                      "PropertyID": "PROP-NESTED"}}}
            ]
        }
        write_json(tmp_path / "loan.json", data)
        assert RLoanLoader(tmp_path).find_by_property_id("PROP-NESTED") is not None
