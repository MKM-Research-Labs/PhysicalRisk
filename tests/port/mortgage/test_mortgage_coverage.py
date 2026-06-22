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

"""Coverage expansion tests for mortgage.py — missing lines 202-205, 228-230."""

from unittest.mock import MagicMock, patch

import pytest

import database
from tests.port.mortgage.conftest import make_generator, write_property_portfolio
from db_helpers import tmp_catchment


@pytest.fixture(autouse=True)
def _iso_catchment(tmp_path):
    """Bind a tmp-rooted backend (catchment "thames") for every test in this module.

    The migrated mortgage generator reads the property portfolio and writes loans through
    ``database``; rooting the backend at ``tmp_path`` means ``write_property_portfolio``
    is read back and loan writes are isolated."""
    with tmp_catchment(tmp_path):
        yield


class TestSingleMortgageFailure:
    """Lines 202-205: exception during _generate_single_mortgage is caught and counted."""

    def test_failed_mortgage_is_counted_and_skipped(self, tmp_path):
        """When _generate_single_mortgage raises, the generator continues and
        increments failed_mortgages."""
        write_property_portfolio(tmp_path, count=3)
        gen = make_generator(tmp_path)

        original_gen = gen._generate_single_mortgage

        def exploding_gen(index, schema, property_info):
            if index == 1:
                raise RuntimeError("synthetic failure")
            return original_gen(index, schema, property_info)

        gen._generate_single_mortgage = exploding_gen

        result = gen.generate()

        assert result["processing_stats"]["failed_mortgages"] == 1
        assert result["processing_stats"]["successful_mortgages"] == 2
        assert len(result["data"]["mortgages"]) == 2

    def test_all_mortgages_fail_returns_empty_list(self, tmp_path):
        write_property_portfolio(tmp_path, count=2)
        gen = make_generator(tmp_path)

        gen._generate_single_mortgage = MagicMock(side_effect=RuntimeError("fail"))

        result = gen.generate()

        assert result["processing_stats"]["failed_mortgages"] == 2
        assert result["data"]["mortgages"] == []


class TestSaveFailure:
    """A failure in the database save is re-raised out of generate()."""

    def test_save_error_is_reraised(self, tmp_path):
        write_property_portfolio(tmp_path, count=1)
        gen = make_generator(tmp_path)

        with patch("database.save_loans", side_effect=OSError("disk full")):
            with pytest.raises(OSError, match="disk full"):
                gen.generate()
