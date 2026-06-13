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

"""Tests for individual pipeline step generators (steps 4, 6, 8, 10)."""

import json

import pytest

from config import config
from tests.port.pipeline.conftest import N_GAUGES, N_PROPERTIES


class TestGaugeTimeSeries:
    """Tests for GaugeTimeSeriesGenerator (step 4)."""

    def test_generates_per_gauge_files(self, pipeline_dir):
        gaugets_dir = pipeline_dir / "gaugets"
        assert gaugets_dir.exists()
        assert len(list(gaugets_dir.glob("GAUGE-*.json"))) >= N_GAUGES

    def test_output_file_has_readings(self, pipeline_dir):
        gauge_files = list((pipeline_dir / "gaugets").glob("GAUGE-*.json"))
        assert len(gauge_files) > 0
        for gf in gauge_files[:3]:
            with open(gf) as f:
                data = json.load(f)
            assert "flood_simulation" in data
            assert len(data["flood_simulation"]["readings"]) > 0

    def test_requires_gauge_portfolio(self, tmp_path):
        from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
        original = config.input_dir
        config.input_dir = tmp_path
        try:
            gen = GaugeTimeSeriesGenerator(tmp_path, verbose=False)
            with pytest.raises(FileNotFoundError):
                gen.generate(simulation_hours=12)
        finally:
            config.input_dir = original


class TestGaugeHistoricalDaily:
    """Tests for generate_all_gauge_histories (step 6)."""

    def test_generates_per_gauge_files(self, pipeline_dir):
        gaugehd_dir = pipeline_dir / "gaugehd"
        assert gaugehd_dir.exists()
        assert len(list(gaugehd_dir.glob("gauge_*_hd.json"))) == N_GAUGES

    def test_output_has_daily_observations(self, pipeline_dir):
        for hf in list((pipeline_dir / "gaugehd").glob("gauge_*_hd.json"))[:3]:
            with open(hf) as f:
                data = json.load(f)
            assert "daily_observations" in data
            assert len(data["daily_observations"]) > 0

    def test_statistics_computed(self, pipeline_dir):
        for hf in list((pipeline_dir / "gaugehd").glob("gauge_*_hd.json"))[:3]:
            with open(hf) as f:
                data = json.load(f)
            assert "statistics" in data
            assert "mean_level" in data["statistics"]
            assert "max_level" in data["statistics"]


class TestPropertyTimeSeries:
    """Tests for PropertyTimeSeriesGenerator (step 8)."""

    def test_generates_per_property_files(self, pipeline_dir):
        pts_dir = pipeline_dir / "propertyts"
        assert pts_dir.exists()
        assert (pts_dir / "portfolio_flood_summary.json").exists()

    def test_portfolio_summary_has_statistics(self, pipeline_dir):
        with open(pipeline_dir / "propertyts" / "portfolio_flood_summary.json") as f:
            data = json.load(f)
        s = data["summary"]
        assert "total_properties" in s
        assert s["total_properties"] == N_PROPERTIES
        assert "total_gauges" in s

    def test_per_property_files_have_flood_data(self, pipeline_dir):
        prop_files = list((pipeline_dir / "propertyts").glob("PROP-*.json"))
        if not prop_files:
            pytest.skip("No per-property files generated (may have 0 floods)")
        for pf in prop_files[:3]:
            with open(pf) as f:
                data = json.load(f)
            assert "property_id" in data
            assert "nearest_gauges" in data
            assert "flood_events" in data


class TestCounterparty:
    """Tests for CounterpartyPortfolioGenerator (step 10)."""

    def test_generates_counterparty_file(self, pipeline_dir):
        assert (pipeline_dir / "counterparty.json").exists()

    def test_all_counterparties_have_party_id(self, pipeline_dir):
        with open(pipeline_dir / "counterparty.json") as f:
            data = json.load(f)
        counterparties = data["counterparties"]
        assert len(counterparties) > 0
        for ctpy in counterparties:
            assert ctpy["CounterpartySet"]["Party"]["PartyID"].startswith("CTPY-")

    def test_cdm_structure(self, pipeline_dir):
        with open(pipeline_dir / "counterparty.json") as f:
            data = json.load(f)
        ctpy = data["counterparties"][0]["CounterpartySet"]
        assert "Party" in ctpy
        assert "PartyID" in ctpy["Party"]
        assert "ContactInformation" in ctpy["Party"]

    def test_custom_count(self, tmp_path):
        from port.src.counterparty import CounterpartyPortfolioGenerator
        gen = CounterpartyPortfolioGenerator(output_dir=tmp_path, verbose=False)
        # +1 REIT prepended to the external pool of size ``count``
        result = gen.generate(count=3)
        assert len(result["data"]) == 4


class TestNostressFlag:
    """Tests for --nostress flag behaviour in cmd_port."""

    def _make_args(self, **kwargs):
        """Build a minimal args namespace for cmd_port.

        Note ``catchment_id="thames"`` — without it ``resolve_catchment``
        falls through to an interactive ``input()`` prompt which raises
        OSError under pytest's stdout capture.
        """
        import argparse
        defaults = dict(
            all=False, gauges=False, properties=False, mortgages=False,
            gaugets=False, gaugehd=False, hazard=False,
            propertyts=False, propertytsd=False, propertytse=False,
            propertyhc=False, propertyshd=False, propertyshe=False,
            counterparties=False, blotter=False, stressm=False,
            # Commercial + typhoon stages added later — orchestrator reads
            # all of these unconditionally when assembling segment_flags.
            commercial=False, commercialts=False, commercialtsd=False,
            commercialtse=False, commercialhc=False, commercialshd=False,
            commercialshe=False, commercialtsb=False, commercialbri=False,
            propertytsb=False, propertybri=False, typhoon=False,
            # Wind-coupled peril stages (win/faw/fow) and BRI-anchored
            # combined-peril stages (bow/baw) — orchestrator reads all of
            # these unconditionally when assembling segment_flags.
            propertytsw=False, propertytsfaw=False, propertytsfow=False,
            propertywin=False, propertyfaw=False, propertyfow=False,
            commercialtsw=False, commercialtsfaw=False, commercialtsfow=False,
            commercialwin=False, commercialfaw=False, commercialfow=False,
            propertytsbow=False, propertytsbaw=False,
            propertybow=False, propertybaw=False,
            commercialtsbow=False, commercialtsbaw=False,
            commercialbow=False, commercialbaw=False,
            fire=False, seismic=False,
            num_typhoon_events=10, num_typhoon_particles=10,
            typhoon_seed=42, typhoon_no_plausibility=False,
            train_classifiers=False, nostress=False,
            gauge_id=None, strict=False, pdf=False,
            num_properties=2, num_gauges=2, num_storms=10,
            simulation_hours=12, history_years=1,
            tail_weight=2.0, distribution='gev', verbose=False,
            catchment_id="thames",
        )
        defaults.update(kwargs)
        return argparse.Namespace(**defaults)

    def test_nostress_flag_exists_in_parser(self):
        """--nostress must be a registered argument on the port subparser."""
        import argparse
        from app.commands.port import register_parser
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        register_parser(sub)
        args = parser.parse_args(['port', '--all', '--nostress'])
        assert args.nostress is True

    def test_nostress_skips_stressm_when_all(self, port_admin_pw):
        """With --all --nostress, generate_stressm must not be called.

        Uses the ``port_admin_pw`` fixture to authenticate via
        ``MKM_PORT_ADMIN_PASSWORD`` env var rather than mocking
        ``_authenticate`` — the password gate is exercised, not bypassed.
        """
        import unittest.mock as mock
        from app.commands.port import cmd_port

        args = self._make_args(all=True, nostress=True)

        with mock.patch('port.src.stressm.generate_stressm') as mock_stressm, \
             mock.patch('port.src.gauge.GaugePortfolioGenerator') as mg, \
             mock.patch('port.src.property.PropertyPortfolioGenerator') as mp, \
             mock.patch('port.src.mortgage.MortgagePortfolioGenerator') as mm, \
             mock.patch('port.src.gauge.gaugets.GaugeTimeSeriesGenerator') as mgt, \
             mock.patch('port.src.gauge.gaugehd.generate_all_gauge_histories') as mhd, \
             mock.patch('port.src.hazard.build_hazard_curves') as mhz, \
             mock.patch('port.src.property.propertyts.PropertyTimeSeriesGenerator') as mpts, \
             mock.patch('port.src.property.propertyhc.PropertyHazardCurveGenerator') as mphc, \
             mock.patch('port.src.counterparty.CounterpartyPortfolioGenerator') as mctpy, \
             mock.patch('port.src.gauge.synthetic.SyntheticGaugeGenerator') as msg, \
             mock.patch('port.src.book.generate_thames_central_book',
                        return_value=[]), \
             mock.patch('port.src.book.generate_property_book',
                        return_value=[]), \
             mock.patch('port.src.book.generate_trade_pdfs'), \
             mock.patch('port.src.book.print_book_summary'), \
             mock.patch('app.commands.port._print_port_summary'):
            mg.return_value.generate.return_value = {
                'data': {'flood_gauges': [1, 2]}, 'processing_stats': {}}
            mp.return_value.generate.return_value = {
                'data': {'properties': [1, 2]}, 'processing_stats': {}}
            mm.return_value.generate.return_value = {
                'data': {'mortgages': [1, 2]}, 'processing_stats': {}}
            mgt.return_value.generate.return_value = {
                'data': {'num_gauges': 2, 'num_timesteps': 24},
                'simulation_parameters': {'simulation_hours': 12}}
            mhd.return_value = [1, 2]
            mhz.return_value = {'summary': {
                'num_gauges': 2, 'num_storms': 10,
                'avg_annual_prob_alert': 0.05,
                'avg_annual_prob_warning': 0.02,
                'avg_annual_prob_severe': 0.01}}
            mpts.return_value.generate.return_value = {
                'total_properties': 2, 'properties_with_floods': 1,
                'total_flood_events': 3, 'max_depth_m': 0.5, 'max_damage_ratio': 0.1}
            mphc.return_value.generate.return_value = {
                'total_properties': 2, 'properties_with_gev': 2,
                'properties_with_floor': 0, 'properties_skipped': 0,
                'avg_basis_bps': 30.0, 'avg_transmission_rate': 0.5}
            mctpy.return_value.generate.return_value = {'metadata': {}, 'data': []}
            msg.return_value.generate.return_value = {'count': 0, 'gauge_ids': []}
            cmd_port(args)

        mock_stressm.assert_not_called()

    def test_explicit_stressm_flag_runs_despite_nostress(self, port_admin_pw):
        """--stressm alone must always run stressm regardless of --nostress.

        Uses the ``port_admin_pw`` fixture for proper authentication and
        mocks every generator the prerequisite chain may invoke
        (synthetic_gauges, properties, gaugehd etc.) — without these
        mocks ``cmd_port`` would write to ``data/input/<catchment>/``
        even though we only care about whether ``generate_stressm`` is
        called (regression: 2026-05-04 incident).
        """
        import unittest.mock as mock
        from app.commands.port import cmd_port

        args = self._make_args(stressm=True, nostress=True)

        stressm_summary = {
            'num_sequences': 10, 'num_gauges': 2, 'type_counts': {},
            'alert_sequences': 1, 'warning_sequences': 1, 'severe_sequences': 0,
            'elapsed_seconds': 1.0,
        }
        with mock.patch('port.src.stressm.generate_stressm',
                        return_value=stressm_summary) as mock_stressm, \
             mock.patch('port.src.gauge.GaugePortfolioGenerator') as mg, \
             mock.patch('port.src.property.PropertyPortfolioGenerator') as mp, \
             mock.patch('port.src.mortgage.MortgagePortfolioGenerator') as mm, \
             mock.patch('port.src.gauge.gaugets.GaugeTimeSeriesGenerator') as mgt, \
             mock.patch('port.src.gauge.gaugehd.generate_all_gauge_histories') as mhd, \
             mock.patch('port.src.hazard.build_hazard_curves') as mhz, \
             mock.patch('port.src.property.propertyts.PropertyTimeSeriesGenerator') as mpts, \
             mock.patch('port.src.property.propertyhc.PropertyHazardCurveGenerator') as mphc, \
             mock.patch('port.src.counterparty.CounterpartyPortfolioGenerator') as mctpy, \
             mock.patch('port.src.gauge.synthetic.SyntheticGaugeGenerator') as msg, \
             mock.patch('port.src.book.generate_thames_central_book',
                        return_value=[]), \
             mock.patch('port.src.book.generate_property_book',
                        return_value=[]), \
             mock.patch('port.src.book.generate_trade_pdfs'), \
             mock.patch('port.src.book.print_book_summary'), \
             mock.patch('app.commands.port._print_port_summary'):
            mg.return_value.generate.return_value = {
                'data': {'flood_gauges': [1, 2]}, 'processing_stats': {}}
            mp.return_value.generate.return_value = {
                'data': {'properties': [1, 2]}, 'processing_stats': {}}
            mm.return_value.generate.return_value = {
                'data': {'mortgages': [1, 2]}, 'processing_stats': {}}
            mgt.return_value.generate.return_value = {
                'data': {'num_gauges': 2, 'num_timesteps': 24},
                'simulation_parameters': {'simulation_hours': 12}}
            mhd.return_value = [1, 2]
            mhz.return_value = {'summary': {
                'num_gauges': 2, 'num_storms': 10,
                'avg_annual_prob_alert': 0.05,
                'avg_annual_prob_warning': 0.02,
                'avg_annual_prob_severe': 0.01}}
            mpts.return_value.generate.return_value = {
                'total_properties': 2, 'properties_with_floods': 1,
                'total_flood_events': 3, 'max_depth_m': 0.5, 'max_damage_ratio': 0.1}
            mphc.return_value.generate.return_value = {
                'total_properties': 2, 'properties_with_gev': 2,
                'properties_with_floor': 0, 'properties_skipped': 0,
                'avg_basis_bps': 30.0, 'avg_transmission_rate': 0.5}
            mctpy.return_value.generate.return_value = {'metadata': {}, 'data': []}
            msg.return_value.generate.return_value = {'count': 0, 'gauge_ids': []}
            cmd_port(args)

        mock_stressm.assert_called_once()
