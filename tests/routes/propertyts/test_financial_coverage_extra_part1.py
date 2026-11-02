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

"""Coverage tests for routes/propertyts/financial.py — PRS matching + loading.

Split from test_financial_coverage_extra.py (~666 lines) so each part
is around 200 lines.  Shared helpers and the ``_build_client`` factory
live in ``_financial_coverage_helpers.py``.
"""

import json

import pytest

from tests.routes.propertyts._financial_coverage_helpers import (
    _build_client,
    _make_mortgage,
    _make_prop_details,
    _make_prop_flood,
    _make_prs_trade,
    write_gauge_responses,
)
from tests.routes.propertyts._helpers import PROP_ID, SEQ_ID, STORM_ID

# ===========================================================================
# REIT hedge payouts follow the gauge trigger
# ===========================================================================

class TestHedgeTrigger:
    """A REIT hedge pays when its gauge reaches severe in the storm."""

    def _client(self, tmp_path, monkeypatch, trades, severe_storms=None):
        return _build_client(
            tmp_path, monkeypatch,
            prop_flood=_make_prop_flood(),
            property_json=_make_prop_details(),
            mortgage_json=_make_mortgage(),
            prs_trades=trades,
            severe_storms=severe_storms,
        )

    def test_hedge_pays_when_gauge_reaches_severe(self, tmp_path, monkeypatch):
        trade = _make_prs_trade('PRS-HIT', 'GAUGE-001', PROP_ID, notional=300_000)
        client = self._client(tmp_path, monkeypatch, [trade])
        prop = client.get(f'/api/v1/propertyts/{SEQ_ID}/portfolio-impact').get_json()['properties'][0]
        assert prop['prs_payout'] == 300_000
        assert prop['prs_trades'][0]['triggered'] is True

    def test_flooded_property_gets_nothing_when_gauge_stays_below_severe(
            self, tmp_path, monkeypatch):
        """The property floods, but the contract trigger is the gauge."""
        trade = _make_prs_trade('PRS-MISS', 'GAUGE-001', PROP_ID, notional=300_000)
        client = self._client(tmp_path, monkeypatch, [trade], severe_storms={})
        data = client.get(f'/api/v1/propertyts/{SEQ_ID}/portfolio-impact').get_json()
        prop = data['properties'][0]
        assert prop['prs_payout'] == 0
        assert prop['prs_trades'][0]['triggered'] is False
        assert data['derivatives']['num_trades_triggered'] == 0
        assert data['derivatives']['total_prs_notional'] == 300_000

    def test_desk_gauge_trade_is_not_a_reit_payout(self, tmp_path, monkeypatch):
        """A desk gauge trade on the property's gauge is not the REIT's."""
        trade = _make_prs_trade('PRS-DESK', 'GAUGE-001', '', notional=100_000,
                                trade_type='PRS')
        client = self._client(tmp_path, monkeypatch, [trade])
        prop = client.get(f'/api/v1/propertyts/{SEQ_ID}/portfolio-impact').get_json()['properties'][0]
        assert prop['prs_trades'] == []
        assert prop['prs_payout'] == 0


class TestLoadAllPrsTrades:

    def test_missing_prs_dir_skips_enrichment(self, tmp_path, monkeypatch):
        """When the prs/ subdir does not exist, derivatives are all zeros."""
        pf = _make_prop_flood()
        client = _build_client(
            tmp_path, monkeypatch,
            prop_flood=pf,
            property_json=_make_prop_details(),
            mortgage_json=_make_mortgage(),
            include_prs_dir=False,
        )
        r = client.get(f'/api/v1/propertyts/{SEQ_ID}/portfolio-impact')
        assert r.status_code == 200
        data = r.get_json()
        assert data['derivatives']['total_prs_payout'] == 0
        assert data['derivatives']['num_trades_triggered'] == 0
        assert data['properties'][0]['prs_trades'] == []

    def test_corrupt_prs_file_is_skipped(self, tmp_path, monkeypatch):
        """A corrupt PRS JSON file is logged and skipped, not fatal."""
        from config import config

        pts_dir = tmp_path / 'propertyts'
        pts_dir.mkdir()
        gaugets_dir = tmp_path / 'gaugets'
        gaugets_dir.mkdir()
        output_dir = tmp_path / 'output'
        output_dir.mkdir()
        prs_dir = tmp_path / 'prs'  # database resolves prs_trade under input_dir/prs
        prs_dir.mkdir()

        (pts_dir / f'{PROP_ID}.json').write_text(json.dumps(_make_prop_flood()))
        (tmp_path / 'property.json').write_text(
            json.dumps(_make_prop_details()))
        (tmp_path / 'loan.json').write_text(json.dumps(_make_mortgage()))
        write_gauge_responses(gaugets_dir, {'GAUGE-001': [SEQ_ID]})

        # One valid trade, one corrupt, plus a stray non-PRS file (skipped).
        good = _make_prs_trade('PRS-GOOD', 'GAUGE-001', PROP_ID, 200_000)
        (prs_dir / 'PRS-GOOD.json').write_text(json.dumps(good))
        (prs_dir / 'PRS-BROKEN.json').write_text('{not valid json')
        (prs_dir / 'notes.json').write_text(json.dumps({'not': 'a trade'}))

        monkeypatch.setattr(config, 'get_input_dir', lambda: tmp_path)
        monkeypatch.setattr(config, 'get_gaugets_dir', lambda: gaugets_dir)
        monkeypatch.setattr(config, 'get_input_path',
                            lambda f: tmp_path / f)
        monkeypatch.setattr(
            config, 'get_reports_dir',
            lambda subdir=None: (output_dir / subdir) if subdir else output_dir,
        )

        from server import create_app
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()

        r = client.get(f'/api/v1/propertyts/{SEQ_ID}/portfolio-impact')
        assert r.status_code == 200
        data = r.get_json()
        # Only the good trade contributes
        assert data['derivatives']['num_trades_triggered'] == 1
        assert data['derivatives']['total_prs_notional'] == 200_000

    def test_trade_with_empty_gauge_basket(self, tmp_path, monkeypatch):
        """A hedge with no gauge can never trigger, so it is left out."""
        trade = _make_prs_trade(
            swap_id='PRS-NO-GAUGE',
            gauge_id=None,  # empty basket
            property_id=PROP_ID,
            notional=150_000,
        )
        client = _build_client(
            tmp_path, monkeypatch,
            prop_flood=_make_prop_flood(),
            property_json=_make_prop_details(),
            mortgage_json=_make_mortgage(),
            prs_trades=[trade],
        )
        r = client.get(f'/api/v1/propertyts/{SEQ_ID}/portfolio-impact')
        prop = r.get_json()['properties'][0]
        assert prop['prs_payout'] == 0
        assert prop['prs_trades'] == []


# ===========================================================================
# _load_gauge_elevations — fallback and exception paths
# ===========================================================================

