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

"""Tests for individual pipeline step generators (steps 4, 6, 8, 10). (part 2 of 2)"""

import json

import pytest

from config import config
from tests.port.pipeline.conftest import N_GAUGES, N_PROPERTIES


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
            num_properties=2, num_gauges=2, num_commercial=2,
            num_storms=10, num_sims=10,
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
             mock.patch('port.src.commercial.CommercialPortfolioGenerator') as mcom, \
             mock.patch('port.src.commercial_loan.CommercialLoanPortfolioGenerator') as mcoml, \
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
            # Commercial portfolio now runs under --all (asymmetry removed); mock
            # it so commercial.json is not written and the downstream commercial
            # stages (gated on commercial_exists) stay skipped.
            mcom.return_value.generate.return_value = {
                'data': {'commercial_assets': []}, 'processing_stats': {}}
            mcoml.return_value.generate.return_value = {
                'data': {'commercial_loans': []}}
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
             mock.patch('port.src.commercial.CommercialPortfolioGenerator') as mcom, \
             mock.patch('port.src.commercial_loan.CommercialLoanPortfolioGenerator') as mcoml, \
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
            # Commercial portfolio now runs under --all (asymmetry removed); mock
            # it so commercial.json is not written and the downstream commercial
            # stages (gated on commercial_exists) stay skipped.
            mcom.return_value.generate.return_value = {
                'data': {'commercial_assets': []}, 'processing_stats': {}}
            mcoml.return_value.generate.return_value = {
                'data': {'commercial_loans': []}}
            cmd_port(args)

        mock_stressm.assert_called_once()
