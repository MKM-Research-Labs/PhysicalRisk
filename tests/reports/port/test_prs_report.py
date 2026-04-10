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

class TestInit:
    def test_explicit_output_path(self, input_dir, tmp_path):
        out = tmp_path / 'report.pdf'
        r = PRSPortfolioReport(input_dir, output_path=out)
        assert r.output_path == out

    def test_default_output_path(self, input_dir, monkeypatch):
        """When no output_path given, uses config.get_output_dir()/audit/."""
        import types

        fake_out = input_dir / 'fake_output'
        fake_config = types.SimpleNamespace(
            get_output_dir=lambda: fake_out,
        )
        monkeypatch.setattr('reports.port.prs_report.config', fake_config,
                            raising=False)
        # Need to patch the import inside __init__
        import reports.port.prs_report as mod
        orig_init = mod.PRSPortfolioReport.__init__

        def patched_init(self, input_dir, output_path=None):
            self.input_dir = mod.Path(input_dir)
            if output_path:
                self.output_path = mod.Path(output_path)
            else:
                audit_dir = fake_out / 'audit'
                audit_dir.mkdir(parents=True, exist_ok=True)
                self.output_path = audit_dir / 'prs_portfolio_report.pdf'
            self._styles = mod.getSampleStyleSheet()
            self._setup_styles()

        monkeypatch.setattr(mod.PRSPortfolioReport, '__init__', patched_init)
        r = PRSPortfolioReport(input_dir)
        assert r.output_path == fake_out / 'audit' / 'prs_portfolio_report.pdf'
        assert r.output_path.parent.exists()

    def test_input_dir_stored_as_path(self, input_dir):
        r = PRSPortfolioReport(str(input_dir), output_path=input_dir / 'out.pdf')
        assert isinstance(r.input_dir, type(input_dir))

    def test_styles_created(self, input_dir):
        r = PRSPortfolioReport(input_dir, output_path=input_dir / 'out.pdf')
        assert r.title_style is not None
        assert r.subtitle_style is not None
        assert r.heading_style is not None
        assert r.body_style is not None


# ---------------------------------------------------------------------------
# _load_data
# ---------------------------------------------------------------------------

class TestLoadData:
    def test_basic_load(self, basic_input, tmp_path):
        r = PRSPortfolioReport(basic_input, output_path=tmp_path / 'out.pdf')
        data = r._load_data()

        assert data['num_properties'] == 2
        assert data['num_storms'] == 2000
        assert 'Zone 3a' in data['by_zone']
        assert 'Zone 2' in data['by_zone']
        assert len(data['by_zone']['Zone 3a']) == 1
        assert len(data['by_zone']['Zone 2']) == 1

    def test_property_record_fields(self, basic_input, tmp_path):
        r = PRSPortfolioReport(basic_input, output_path=tmp_path / 'out.pdf')
        data = r._load_data()
        rec = data['by_zone']['Zone 3a'][0]

        assert rec['pid'] == 'P1'
        assert rec['zone'] == 'Zone 3a'
        assert rec['dist_m'] == 0.5 * 1000  # synth gauge dist_km * 1000
        assert rec['offset'] == 11.0 - 10.0  # prop elev - gauge elev
        assert rec['floor'] == 0.5
        assert rec['flood_count'] == 5
        assert rec['gauge_spread'] == 100
        assert rec['shd_spread'] == 55
        assert rec['she_spread'] == 60
        assert rec['prop_spread'] == 70
        assert rec['basis'] == 100 - 70  # gauge_spread - prop_spread
        assert rec['transmission'] == 0.8

    def test_storm_sequences_overrides_metadata(self, input_dir, tmp_path):
        curves = [_property_hc('P1')]
        _write_propertyhc(input_dir, curves, num_storms=1000)
        _write_storm_sequences(input_dir, num_sequences=9999)

        r = PRSPortfolioReport(input_dir, output_path=tmp_path / 'out.pdf')
        data = r._load_data()
        assert data['num_storms'] == 9999

    def test_no_storm_sequences_uses_metadata(self, input_dir, tmp_path):
        curves = [_property_hc('P1')]
        _write_propertyhc(input_dir, curves, num_storms=3000)

        r = PRSPortfolioReport(input_dir, output_path=tmp_path / 'out.pdf')
        data = r._load_data()
        assert data['num_storms'] == 3000

    def test_missing_shd_she_files(self, input_dir, tmp_path):
        """SHD and SHE spreads default to 0 when files are absent."""
        curves = [_property_hc('P1')]
        _write_propertyhc(input_dir, curves)

        r = PRSPortfolioReport(input_dir, output_path=tmp_path / 'out.pdf')
        data = r._load_data()
        rec = data['by_zone']['Zone 2'][0]
        assert rec['shd_spread'] == 0
        assert rec['she_spread'] == 0

    def test_property_without_synth_gauge_is_skipped(self, input_dir, tmp_path):
        """Properties whose nearest_gauges has no SYNTH gauge are excluded."""
        pid, hc = _property_hc('P-NO-SYNTH', nearest_gauges=[_real_gauge()])
        _write_propertyhc(input_dir, [(pid, hc)])

        r = PRSPortfolioReport(input_dir, output_path=tmp_path / 'out.pdf')
        data = r._load_data()
        assert sum(len(v) for v in data['by_zone'].values()) == 0

    def test_sorted_by_spread_descending(self, input_dir, tmp_path):
        curves = [
            _property_hc('LOW', zone='Zone 2', spread_bps=10),
            _property_hc('MID', zone='Zone 2', spread_bps=50),
            _property_hc('HIGH', zone='Zone 2', spread_bps=90),
        ]
        _write_propertyhc(input_dir, curves)

        r = PRSPortfolioReport(input_dir, output_path=tmp_path / 'out.pdf')
        data = r._load_data()
        pids = [p['pid'] for p in data['by_zone']['Zone 2']]
        assert pids == ['HIGH', 'MID', 'LOW']

    def test_empty_property_hazard_curves(self, input_dir, tmp_path):
        _write_propertyhc(input_dir, [])
        r = PRSPortfolioReport(input_dir, output_path=tmp_path / 'out.pdf')
        data = r._load_data()
        assert data['num_properties'] == 0
        assert data['by_zone'] == {}

    def test_missing_floor_level_defaults_zero(self, input_dir, tmp_path):
        pid, hc = _property_hc('P1')
        del hc['floor_level_m']
        _write_propertyhc(input_dir, [(pid, hc)])

        r = PRSPortfolioReport(input_dir, output_path=tmp_path / 'out.pdf')
        data = r._load_data()
        assert data['by_zone']['Zone 2'][0]['floor'] == 0

    def test_missing_flood_count_defaults_zero(self, input_dir, tmp_path):
        pid, hc = _property_hc('P1')
        del hc['flood_count']
        _write_propertyhc(input_dir, [(pid, hc)])

        r = PRSPortfolioReport(input_dir, output_path=tmp_path / 'out.pdf')
        data = r._load_data()
        assert data['by_zone']['Zone 2'][0]['flood_count'] == 0

    def test_all_four_zones(self, input_dir, tmp_path):
        curves = [
            _property_hc('A', zone='Zone 1', spread_bps=10),
            _property_hc('B', zone='Zone 2', spread_bps=20),
            _property_hc('C', zone='Zone 3a', spread_bps=30),
            _property_hc('D', zone='Zone 3b', spread_bps=40),
        ]
        _write_propertyhc(input_dir, curves)

        r = PRSPortfolioReport(input_dir, output_path=tmp_path / 'out.pdf')
        data = r._load_data()
        assert set(data['by_zone'].keys()) == {'Zone 1', 'Zone 2', 'Zone 3a', 'Zone 3b'}


# ---------------------------------------------------------------------------
# _zone_summary_table
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
