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

"""Tests for src/reports/port/prs_report.py — PRSPortfolioReport."""

import json

import pytest
from reportlab.platypus import Paragraph, Spacer, Table, PageBreak

from reports.port.prs_report import PRSPortfolioReport


# ---------------------------------------------------------------------------
# Helpers to build test data on disk
# ---------------------------------------------------------------------------

def _synth_gauge(dist_km=0.5, elev=10.0, transmission=0.8):
    return {
        'gauge_id': 'SYNTH-001',
        'distance_km': dist_km,
        'gauge_elevation_m': elev,
        'flood_transmission_rate': transmission,
    }


def _real_gauge(gid='GAUGE-001', dist_km=1.0, elev=12.0):
    return {'gauge_id': gid, 'distance_km': dist_km, 'gauge_elevation_m': elev}


def _property_hc(pid='PROP-001', zone='Zone 2', elev=12.5, floor=0.5,
                  flood_count=3, gauge_spread=80, spread_bps=50,
                  nearest_gauges=None):
    if nearest_gauges is None:
        nearest_gauges = [_real_gauge(), _synth_gauge()]
    return pid, {
        'flood_zone': zone,
        'elevation_m': elev,
        'floor_level_m': floor,
        'flood_count': flood_count,
        'spread_decomposition': {'gauge_spread_bps': gauge_spread},
        'nearest_gauges': nearest_gauges,
        'term_structure': {'severe': {'prs_spread_bps': [spread_bps]}},
    }


def _write_propertyhc(d, curves, num_storms=1000):
    (d / 'propertyhc.json').write_text(json.dumps({
        'metadata': {'num_storms': num_storms},
        'property_hazard_curves': dict(curves),
    }))


def _write_propertyshd(d, curves):
    (d / 'propertyshd.json').write_text(json.dumps({
        'property_hazard_curves': dict(curves),
    }))


def _write_propertyshe(d, curves):
    (d / 'propertyshe.json').write_text(json.dumps({
        'property_hazard_curves': dict(curves),
    }))


def _write_storm_sequences(d, num_sequences=5000):
    (d / 'storm_sequences.json').write_text(json.dumps({
        'num_sequences': num_sequences,
    }))


def _shd_she_entry(pid, spread_bps=30):
    return pid, {
        'term_structure': {'severe': {'prs_spread_bps': [spread_bps]}},
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def input_dir(tmp_path):
    d = tmp_path / 'catchment_x'
    d.mkdir()
    return d


@pytest.fixture
def basic_input(input_dir):
    """Input directory with two properties in different zones, plus SHD/SHE."""
    curves = [
        _property_hc('P1', zone='Zone 3a', elev=11.0, flood_count=5,
                      gauge_spread=100, spread_bps=70),
        _property_hc('P2', zone='Zone 2', elev=13.0, flood_count=1,
                      gauge_spread=40, spread_bps=20),
    ]
    _write_propertyhc(input_dir, curves, num_storms=2000)
    _write_propertyshd(input_dir, [_shd_she_entry('P1', 55), _shd_she_entry('P2', 15)])
    _write_propertyshe(input_dir, [_shd_she_entry('P1', 60), _shd_she_entry('P2', 18)])
    return input_dir


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------

class TestZoneSummaryTable:
    def test_returns_table(self, basic_input, tmp_path):
        r = PRSPortfolioReport(basic_input, output_path=tmp_path / 'out.pdf')
        data = r._load_data()
        t = r._zone_summary_table(data)
        assert isinstance(t, Table)

    def test_empty_zones_show_zero_count(self, input_dir, tmp_path):
        curves = [_property_hc('P1', zone='Zone 2')]
        _write_propertyhc(input_dir, curves)

        r = PRSPortfolioReport(input_dir, output_path=tmp_path / 'out.pdf')
        data = r._load_data()
        t = r._zone_summary_table(data)
        # Table rows: header + 4 zones
        assert len(t._cellvalues) == 5  # header + Zone 3b, 3a, 2, 1

    def test_stats_calculation(self, input_dir, tmp_path):
        curves = [
            _property_hc('A', zone='Zone 2', flood_count=4, gauge_spread=100,
                          spread_bps=60),
            _property_hc('B', zone='Zone 2', flood_count=6, gauge_spread=80,
                          spread_bps=40),
        ]
        _write_propertyhc(input_dir, curves)

        r = PRSPortfolioReport(input_dir, output_path=tmp_path / 'out.pdf')
        data = r._load_data()
        t = r._zone_summary_table(data)

        # Zone 2 is 3rd data row (Zone 3b, 3a, 2, 1), index=3
        zone2_row = t._cellvalues[3]
        assert zone2_row[0] == 'Zone 2'
        assert zone2_row[1] == 2  # count
        assert zone2_row[2] == '5'  # avg floods (4+6)/2
        assert zone2_row[3] == '50.0'  # avg spread (60+40)/2
        assert zone2_row[4] == '40.0'  # min
        assert zone2_row[5] == '60.0'  # max
        assert zone2_row[6] == '90.0'  # avg gauge (100+80)/2
        assert zone2_row[7] == '40.0'  # avg basis (100-60 + 80-40)/2 = 40


# ---------------------------------------------------------------------------
# _zone_property_table
# ---------------------------------------------------------------------------

class TestZonePropertyTable:
    def test_returns_table(self, basic_input, tmp_path):
        r = PRSPortfolioReport(basic_input, output_path=tmp_path / 'out.pdf')
        data = r._load_data()
        props = data['by_zone']['Zone 3a']
        t = r._zone_property_table(props, data['num_storms'])
        assert isinstance(t, Table)

    def test_row_count(self, basic_input, tmp_path):
        r = PRSPortfolioReport(basic_input, output_path=tmp_path / 'out.pdf')
        data = r._load_data()
        props = data['by_zone']['Zone 3a']
        t = r._zone_property_table(props, data['num_storms'])
        # header + 1 property
        assert len(t._cellvalues) == 2

    def test_property_id_truncated(self, input_dir, tmp_path):
        long_pid = 'A' * 30
        curves = [_property_hc(long_pid, zone='Zone 2')]
        _write_propertyhc(input_dir, curves)

        r = PRSPortfolioReport(input_dir, output_path=tmp_path / 'out.pdf')
        data = r._load_data()
        props = data['by_zone']['Zone 2']
        t = r._zone_property_table(props, 1000)
        assert t._cellvalues[1][0] == long_pid[:16]

    def test_formatting(self, input_dir, tmp_path):
        curves = [_property_hc('P1', zone='Zone 2', elev=12.5, flood_count=3,
                                gauge_spread=80, spread_bps=50)]
        _write_propertyhc(input_dir, curves)

        r = PRSPortfolioReport(input_dir, output_path=tmp_path / 'out.pdf')
        data = r._load_data()
        props = data['by_zone']['Zone 2']
        t = r._zone_property_table(props, 1000)
        row = t._cellvalues[1]

        assert row[0] == 'P1'  # pid (short, no truncation)
        assert row[1] == '500'  # dist_m = 0.5km * 1000
        assert row[2] == '2.50'  # offset = 12.5 - 10.0
        assert row[3] == '0.50'  # floor
        assert row[4] == '3'  # flood_count
        assert row[5] == '80.0%'  # transmission
        assert row[6] == '80.0'  # gauge_spread
        assert row[9] == '50.0'  # prop_spread
        assert row[10] == '+30.0'  # basis = 80 - 50, positive with +

    def test_column_widths(self, basic_input, tmp_path):
        r = PRSPortfolioReport(basic_input, output_path=tmp_path / 'out.pdf')
        data = r._load_data()
        props = data['by_zone']['Zone 3a']
        t = r._zone_property_table(props, 1000)
        assert t._colWidths == [105, 50, 55, 45, 45, 45, 55, 55, 55, 55, 55]


# ---------------------------------------------------------------------------
# generate (end-to-end)
# ---------------------------------------------------------------------------

class TestGenerate:
    def test_generates_pdf(self, basic_input, tmp_path):
        out = tmp_path / 'report.pdf'
        r = PRSPortfolioReport(basic_input, output_path=out)
        result = r.generate()
        assert result == out
        assert out.exists()
        assert out.stat().st_size > 0

    def test_pdf_content_header(self, basic_input, tmp_path):
        out = tmp_path / 'report.pdf'
        PRSPortfolioReport(basic_input, output_path=out).generate()
        raw = out.read_bytes()
        assert raw[:5] == b'%PDF-'

    def test_empty_data_still_generates(self, input_dir, tmp_path):
        _write_propertyhc(input_dir, [])
        out = tmp_path / 'report.pdf'
        r = PRSPortfolioReport(input_dir, output_path=out)
        result = r.generate()
        assert result == out
        assert out.exists()

    def test_all_zones_populated(self, input_dir, tmp_path):
        curves = [
            _property_hc('A', zone='Zone 1'),
            _property_hc('B', zone='Zone 2'),
            _property_hc('C', zone='Zone 3a'),
            _property_hc('D', zone='Zone 3b'),
        ]
        _write_propertyhc(input_dir, curves)
        out = tmp_path / 'report.pdf'
        r = PRSPortfolioReport(input_dir, output_path=out)
        result = r.generate()
        assert result.exists()
        assert result.stat().st_size > 0

    def test_only_some_zones(self, input_dir, tmp_path):
        """Zones with no properties are skipped, no crash."""
        curves = [_property_hc('X', zone='Zone 3b')]
        _write_propertyhc(input_dir, curves)
        out = tmp_path / 'report.pdf'
        r = PRSPortfolioReport(input_dir, output_path=out)
        assert r.generate().exists()

    def test_many_properties(self, input_dir, tmp_path):
        curves = [
            _property_hc(f'P{i:04d}', zone='Zone 2', spread_bps=i)
            for i in range(50)
        ]
        _write_propertyhc(input_dir, curves)
        out = tmp_path / 'report.pdf'
        r = PRSPortfolioReport(input_dir, output_path=out)
        assert r.generate().exists()

    def test_negative_basis(self, input_dir, tmp_path):
        """Property spread > gauge spread gives negative basis — no crash."""
        curves = [_property_hc('P1', zone='Zone 2', gauge_spread=30, spread_bps=80)]
        _write_propertyhc(input_dir, curves)
        out = tmp_path / 'report.pdf'
        r = PRSPortfolioReport(input_dir, output_path=out)
        assert r.generate().exists()

    def test_negative_offset(self, input_dir, tmp_path):
        """Property below gauge elevation — negative offset, no crash."""
        curves = [_property_hc('P1', zone='Zone 2', elev=8.0)]  # gauge at 10.0
        _write_propertyhc(input_dir, curves)
        out = tmp_path / 'report.pdf'
        r = PRSPortfolioReport(input_dir, output_path=out)
        data = r._load_data()
        assert data['by_zone']['Zone 2'][0]['offset'] == -2.0
        assert r.generate().exists()

    def test_zero_transmission(self, input_dir, tmp_path):
        curves = [_property_hc('P1', zone='Zone 2',
                                nearest_gauges=[
                                    _real_gauge(),
                                    _synth_gauge(transmission=0.0),
                                ])]
        _write_propertyhc(input_dir, curves)
        out = tmp_path / 'report.pdf'
        r = PRSPortfolioReport(input_dir, output_path=out)
        assert r.generate().exists()
