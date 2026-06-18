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

"""Tests for DataLoader._load_hazard_curves, _load_storm_data, _load_counterparty_data."""

import json

from .conftest import write_hazard, write_property_hazard, write_storms, write_counterparty


class TestLoadHazardCurves:

    def test_missing_hazard_file_leaves_hazard_data_none(self, tmp_path):
        from visual.core.data_loader import DataLoader
        dl = DataLoader(input_dir=tmp_path)
        dl._load_hazard_curves()
        assert dl.loaded_data.hazard_data is None

    def test_missing_property_hazard_file_leaves_phc_none(self, tmp_path):
        from visual.core.data_loader import DataLoader
        dl = DataLoader(input_dir=tmp_path)
        dl._load_hazard_curves()
        assert dl.loaded_data.property_hazard_data is None

    def test_corrupt_hazard_file_leaves_hazard_data_none(self, tmp_path):
        from visual.core.data_loader import DataLoader
        from jsonfiles import JSONFileConfig
        (tmp_path / JSONFileConfig.HAZARD_CURVES).write_text("NOT VALID JSON {{")
        dl = DataLoader(input_dir=tmp_path)
        dl._load_hazard_curves()
        assert dl.loaded_data.hazard_data is None

    def test_corrupt_property_hazard_file_leaves_phc_none(self, tmp_path):
        from visual.core.data_loader import DataLoader
        from jsonfiles import JSONFileConfig
        (tmp_path / JSONFileConfig.PROPERTY_HAZARD_CURVES).write_text("NOT VALID JSON {{")
        dl = DataLoader(input_dir=tmp_path)
        dl._load_hazard_curves()
        assert dl.loaded_data.property_hazard_data is None

    def test_valid_hazard_file_populates_hazard_data(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_hazard(tmp_path)
        dl = DataLoader(input_dir=tmp_path)
        dl._load_hazard_curves()
        assert dl.loaded_data.hazard_data is not None
        assert "hazard_curves" in dl.loaded_data.hazard_data


class TestLoadStormData:

    def test_missing_storm_file_leaves_storm_data_none(self, tmp_path):
        from visual.core.data_loader import DataLoader
        dl = DataLoader(input_dir=tmp_path)
        dl._load_storm_data()
        assert dl.loaded_data.storm_data is None

    def test_corrupt_storm_file_leaves_storm_data_none(self, tmp_path):
        from visual.core.data_loader import DataLoader
        from jsonfiles import JSONFileConfig
        (tmp_path / JSONFileConfig.STORM_EVENTS).write_text("NOT VALID JSON {{")
        dl = DataLoader(input_dir=tmp_path)
        dl._load_storm_data()
        assert dl.loaded_data.storm_data is None

    def test_storms_dict_with_storms_key(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_storms(tmp_path)
        dl = DataLoader(input_dir=tmp_path)
        dl._load_storm_data()
        assert dl.loaded_data.storm_data is not None

    def test_storms_list_format(self, tmp_path):
        from visual.core.data_loader import DataLoader
        from jsonfiles import JSONFileConfig
        (tmp_path / JSONFileConfig.STORM_EVENTS).write_text(
            json.dumps([{"storm_id": "EVT-A"}, {"storm_id": "EVT-B"}])
        )
        dl = DataLoader(input_dir=tmp_path)
        dl._load_storm_data()
        assert dl.loaded_data.storm_data is not None

    def test_storms_other_type(self, tmp_path):
        from visual.core.data_loader import DataLoader
        from jsonfiles import JSONFileConfig
        (tmp_path / JSONFileConfig.STORM_EVENTS).write_text(json.dumps("scalar"))
        dl = DataLoader(input_dir=tmp_path)
        dl._load_storm_data()
        assert dl.loaded_data.storm_data is not None


class TestLoadCounterpartyData:

    def test_missing_counterparty_file_leaves_data_none(self, tmp_path):
        from visual.core.data_loader import DataLoader
        dl = DataLoader(input_dir=tmp_path)
        dl._load_counterparty_data()
        assert dl.loaded_data.counterparty_data is None

    def test_corrupt_counterparty_file_leaves_data_none(self, tmp_path):
        from visual.core.data_loader import DataLoader
        from jsonfiles import JSONFileConfig
        (tmp_path / JSONFileConfig.COUNTERPARTY_PORTFOLIO).write_text("NOT VALID JSON {{")
        dl = DataLoader(input_dir=tmp_path)
        dl._load_counterparty_data()
        assert dl.loaded_data.counterparty_data is None

    def test_valid_counterparty_file_loads(self, tmp_path):
        from visual.core.data_loader import DataLoader
        write_counterparty(tmp_path)
        dl = DataLoader(input_dir=tmp_path)
        dl._load_counterparty_data()
        assert dl.loaded_data.counterparty_data is not None
        assert "counterparties" in dl.loaded_data.counterparty_data
