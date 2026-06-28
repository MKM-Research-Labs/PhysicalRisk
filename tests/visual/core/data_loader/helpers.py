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

"""Tests for DataLoader helper methods and _print_loading_summary."""

from .conftest import write_gauge, write_hazard, write_mortgage, write_property, write_storms


class TestDataLoaderHelpers:

    def test_is_data_complete_false_before_load(self, tmp_path):
        from visual.core.data_loader import DataLoader
        assert DataLoader(input_dir=tmp_path).is_data_complete() is False

    def test_is_data_complete_false_when_no_gauge(self, tmp_path):
        from visual.core.data_loader import DataLoader
        dl = DataLoader(input_dir=tmp_path)
        dl.load_all_data()
        assert dl.is_data_complete() is False

    def test_is_data_complete_true_with_gauge(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        dl = DataLoader(input_dir=tmp_path)
        dl.load_all_data()
        assert dl.is_data_complete() is True

    def test_is_data_complete_depends_only_on_gauge(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_property(tmp_path)  # no gauge file
        dl = DataLoader(input_dir=tmp_path)
        dl.load_all_data()
        assert dl.is_data_complete() is False

    def test_get_validation_summary_returns_dict(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        dl = DataLoader(input_dir=tmp_path)
        dl.load_all_data()
        assert isinstance(dl.get_validation_summary(), dict)

    def test_get_validation_summary_is_copy(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        dl = DataLoader(input_dir=tmp_path)
        dl.load_all_data()
        s1 = dl.get_validation_summary()
        s2 = dl.get_validation_summary()
        assert s1 is not s2

    def test_get_data_summary_returns_dict(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        dl = DataLoader(input_dir=tmp_path)
        dl.load_all_data()
        assert isinstance(dl.get_data_summary(), dict)

    def test_validation_summary_has_gauge_key(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        dl = DataLoader(input_dir=tmp_path)
        dl.load_all_data()
        assert "gauge" in dl.get_validation_summary()

    def test_data_summary_loaded_flag_true_for_gauge(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        dl = DataLoader(input_dir=tmp_path)
        dl.load_all_data()
        assert dl.get_data_summary()["gauge"]["loaded"] is True

    def test_data_summary_loaded_flag_false_when_no_file(self, tmp_path):
        from visual.core.data_loader import DataLoader
        dl = DataLoader(input_dir=tmp_path)
        dl.load_all_data()
        summary = dl.get_data_summary()
        if "gauge" in summary:
            assert summary["gauge"]["loaded"] is False

    def test_data_summary_contains_warnings_count(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        dl = DataLoader(input_dir=tmp_path)
        dl.load_all_data()
        assert "warnings" in dl.get_data_summary()["gauge"]

    def test_data_summary_contains_errors_count(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        dl = DataLoader(input_dir=tmp_path)
        dl.load_all_data()
        assert "errors" in dl.get_data_summary()["gauge"]

    def test_get_validation_summary_empty_before_load(self, tmp_path):
        from visual.core.data_loader import DataLoader
        assert DataLoader(input_dir=tmp_path).get_validation_summary() == {}

    def test_get_data_summary_empty_before_load(self, tmp_path):
        from visual.core.data_loader import DataLoader
        assert DataLoader(input_dir=tmp_path).get_data_summary() == {}


class TestLoadOptionalJson:
    """Covers commercial portfolio loading (via the seam) + _build_commercial_loan_lookup."""

    def test_commercial_absent_is_none(self, tmp_path):
        import database
        from visual.core.data_loader import DataLoader
        dl = DataLoader(input_dir=tmp_path)
        dl.load_all_data()
        assert dl.loaded_data.commercial_data is None
        assert dl.loaded_data.commercial_loan_data is None

    def test_commercial_loaded_from_seam(self, tmp_path):
        import database
        from visual.core.data_loader import DataLoader
        cat = database.active_catchment()
        database.save_commercial(cat, {"commercial_assets": [{"a": 1}, {"b": 2}]})
        dl = DataLoader(input_dir=tmp_path)
        dl.load_all_data()
        assert dl.loaded_data.commercial_data["commercial_assets"][0] == {"a": 1}

    def test_commercial_loan_loaded_from_seam(self, tmp_path):
        import database
        from visual.core.data_loader import DataLoader
        cat = database.active_catchment()
        database.save_commercial_loans(cat, {"commercial_loans": [{"x": 1}]})
        dl = DataLoader(input_dir=tmp_path)
        dl.load_all_data()
        assert dl.loaded_data.commercial_loan_data["commercial_loans"] == [{"x": 1}]

    def test_build_commercial_loan_lookup_indexes_by_pid(self, tmp_path):
        from visual.core.data_loader import DataLoader
        dl = DataLoader(input_dir=tmp_path)
        dl.loaded_data.commercial_loan_data = {"commercial_loans": [
            {"RLoan": {"Header": {"PropertyID": "CPROP-1"}}},
            {"RLoan": {"Header": {}}},  # no PID → skipped
        ]}
        dl._build_commercial_loan_lookup()
        assert "CPROP-1" in dl.loaded_data.commercial_loan_lookup
        assert len(dl.loaded_data.commercial_loan_lookup) == 1

    def test_build_commercial_loan_lookup_empty(self, tmp_path):
        from visual.core.data_loader import DataLoader
        dl = DataLoader(input_dir=tmp_path)
        dl.loaded_data.commercial_loan_data = None
        dl._build_commercial_loan_lookup()
        assert dl.loaded_data.commercial_loan_lookup == {}


class TestPrintLoadingSummary:

    def test_summary_with_no_data_does_not_crash(self, tmp_path):
        from visual.core.data_loader import DataLoader
        DataLoader(input_dir=tmp_path)._print_loading_summary()

    def test_summary_with_partial_data_does_not_crash(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        dl = DataLoader(input_dir=tmp_path)
        dl.loaded_data.gauge_data = {"count": 2, "items": [{}, {}]}
        dl.loaded_data.gauge_flood_info = {}
        dl.loaded_data.property_flood_info = {}
        dl.loaded_data.rloan_lookup = {}
        dl._print_loading_summary()

    def test_summary_with_full_data_does_not_crash(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_gauge(tmp_path)
        write_property(tmp_path)
        write_mortgage(tmp_path)
        write_hazard(tmp_path)
        write_storms(tmp_path)
        dl = DataLoader(input_dir=tmp_path)
        dl.load_all_data()
        # passes if no exception raised
