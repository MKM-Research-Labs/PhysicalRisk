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

"""Coverage tests for routes/propertyts/financial.py — PRS matching + loading.

Split from test_financial_coverage_extra.py (~666 lines) so each part
is around 200 lines.  Shared helpers and the ``_build_client`` factory
live in ``_financial_coverage_helpers.py``.
"""

import json

import pytest

from tests.routes.propertyts._helpers import PROP_ID, SEQ_ID, STORM_ID
from tests.routes.propertyts._financial_coverage_helpers import (
    _build_client,
    _make_mortgage,
    _make_prop_details,
    _make_prop_flood,
    _make_prs_trade,
)


# ===========================================================================
# _match_prs_to_properties — gauge matching + dedup
# ===========================================================================

class TestPrsGaugeMatch:
    """Trades without a property_id should match via reference gauge."""

    def test_gauge_only_trade_matches_via_reference_gauge(
            self, tmp_path, monkeypatch):
        """Trade has property_id='' but gauge_id matches property's
        reference gauge → should attach to the property."""
        pf = _make_prop_flood()
        trade = _make_prs_trade(
            swap_id='PRS-GAUGE-ONLY',
            gauge_id='GAUGE-001',
            property_id='',
            notional=100_000,
            trade_type='InterDealerPRS',
        )
        client = _build_client(
            tmp_path, monkeypatch,
            prop_flood=pf,
            property_json=_make_prop_details(),
            mortgage_json=_make_mortgage(),
            prs_trades=[trade],
        )
        r = client.get(f'/api/v1/propertyts/{SEQ_ID}/portfolio-impact')
        assert r.status_code == 200
        data = r.get_json()
        prop = data['properties'][0]
        swap_ids = [t['swap_id'] for t in prop['prs_trades']]
        assert 'PRS-GAUGE-ONLY' in swap_ids
        assert prop['prs_payout'] == 100_000

    def test_direct_and_gauge_match_dedup(self, tmp_path, monkeypatch):
        """A trade with both a matching property_id AND matching gauge_id
        must appear exactly once (swap_id dedup)."""
        pf = _make_prop_flood()
        trade = _make_prs_trade(
            swap_id='PRS-DUP',
            gauge_id='GAUGE-001',
            property_id=PROP_ID,
            notional=300_000,
        )
        client = _build_client(
            tmp_path, monkeypatch,
            prop_flood=pf,
            property_json=_make_prop_details(),
            mortgage_json=_make_mortgage(),
            prs_trades=[trade],
        )
        r = client.get(f'/api/v1/propertyts/{SEQ_ID}/portfolio-impact')
        data = r.get_json()
        prop = data['properties'][0]
        dup_hits = [t for t in prop['prs_trades'] if t['swap_id'] == 'PRS-DUP']
        assert len(dup_hits) == 1
        assert prop['prs_payout'] == 300_000


# ===========================================================================
# _load_all_prs_trades — edge cases
# ===========================================================================

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
        """Trade with empty GaugeBasket → gauge_id='' → direct match only."""
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
        data = r.get_json()
        prop = data['properties'][0]
        # Direct property_id match succeeds despite empty gauge basket
        assert prop['prs_payout'] == 150_000
        assert prop['prs_trades'][0]['swap_id'] == 'PRS-NO-GAUGE'


# ===========================================================================
# _load_gauge_elevations — fallback and exception paths
# ===========================================================================

