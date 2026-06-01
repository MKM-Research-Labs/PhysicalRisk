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

"""
Property flood timeseries — portfolio VaR/ES endpoint.

Computes loss distributions across all 10,000 storm scenarios,
VaR and Expected Shortfall at 95%/99.9%, histograms, and tail storms.
"""

import json
import logging

import numpy as np
from flask import jsonify, request

from config import config
from . import propertyts_bp, _get_propertyts_dir

logger = logging.getLogger(__name__)


@propertyts_bp.route('/propertyts/portfolio-var', methods=['GET', 'OPTIONS'])
def portfolio_var():
    """
    Compute portfolio Value at Risk from all 10,000 storm scenarios.

    For each storm: sums property value reduction and mortgage value
    impairment across all 200 properties. Returns the full loss
    distribution with VaR/ES at 95% and 99%.
    """
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})

    pts_dir = _get_propertyts_dir()
    if not pts_dir.exists():
        return jsonify({
            'status': 'error',
            'message': 'Property flood timeseries not yet generated'
        }), 404

    # Load all storm IDs from storm_sequences.json (storm_multi)
    storms_path = config.get_input_path('storm_sequences.json')
    try:
        with open(storms_path, 'r') as f:
            sdata = json.load(f)
        all_storm_ids = [
            seq['sequence_id']
            for seq in sdata.get('sequences', [])
            if seq.get('sequence_id')
        ]
    except Exception as e:
        logger.warning(f'Could not load storm_sequences.json: {e}')
        return jsonify({'status': 'error', 'message': 'storm_sequences.json not found'}), 404

    # Load property valuations
    prop_path = config.get_input_path('property.json')
    prop_values = {}
    try:
        with open(prop_path, 'r') as f:
            pdata = json.load(f)
        for p in pdata.get('properties', []):
            ph = p.get('PropertyHeader', {})
            pid = ph.get('Header', {}).get('PropertyID', '')
            val = ph.get('Valuation', {}).get('PropertyValue', 0)
            prop_values[pid] = val
    except Exception as e:
        logger.warning(f'Could not load property.json: {e}')

    # Load mortgage data
    mortgage_path = config.get_input_path('loan.json')
    rloan_lookup = {}
    try:
        with open(mortgage_path, 'r') as f:
            mdata = json.load(f)
        for m in mdata.get('loans', []):
            mg = m.get('RLoan', {})
            pid = mg.get('Header', {}).get('PropertyID', '')
            outstanding = mg.get('CurrentStatus', {}).get('OutstandingBalance', 0)
            rloan_lookup[pid] = outstanding
    except Exception as e:
        logger.warning(f'Could not load loan.json: {e}')

    total_portfolio_value = sum(prop_values.values())
    total_portfolio_mortgages = sum(rloan_lookup.values())

    # Accumulate per-storm losses: {storm_id -> {prop_damage, mort_impairment, n_affected}}
    storm_data = {}
    for pf in pts_dir.glob('PROP-*.json'):
        with open(pf, 'r') as f:
            pfdata = json.load(f)

        prop_id = pfdata.get('property_id', pf.stem)
        if prop_id not in prop_values:
            continue

        prop_value = prop_values[prop_id]
        mortgage_bal = rloan_lookup.get(prop_id, 0)

        for event in pfdata.get('flood_events', []):
            depth = event.get('flood_depth_m', 0)
            if depth <= 0:
                continue
            sid = event.get('storm_id', '')
            damage_ratio = event.get('damage_ratio', 0)
            prop_damage = prop_value * damage_ratio
            post_value = prop_value - prop_damage

            # Mortgage impairment: shortfall if post-damage value < outstanding
            mort_impairment = max(0, mortgage_bal - post_value) if mortgage_bal > 0 else 0

            if sid not in storm_data:
                storm_data[sid] = {
                    'property_damage': 0,
                    'mortgage_impairment': 0,
                    'n_affected': 0,
                }
            storm_data[sid]['property_damage'] += prop_damage
            storm_data[sid]['mortgage_impairment'] += mort_impairment
            storm_data[sid]['n_affected'] += 1

    # Build full vectors over all 10,000 storms (most will be zero)
    n_storms = len(all_storm_ids)
    prop_losses = np.zeros(n_storms)
    mort_losses = np.zeros(n_storms)

    for i, sid in enumerate(all_storm_ids):
        if sid in storm_data:
            prop_losses[i] = storm_data[sid]['property_damage']
            mort_losses[i] = storm_data[sid]['mortgage_impairment']

    # Compute VaR and ES for both distributions
    def var_es(losses, q):
        var_val = float(np.percentile(losses, q))
        tail = losses[losses >= var_val] if var_val > 0 else losses[losses > 0]
        es_val = float(np.mean(tail)) if len(tail) > 0 else var_val
        return round(var_val, 2), round(es_val, 2)

    prop_var_95, prop_es_95 = var_es(prop_losses, 95)
    prop_var_999, prop_es_999 = var_es(prop_losses, 99.9)
    mort_var_95, mort_es_95 = var_es(mort_losses, 95)
    mort_var_999, mort_es_999 = var_es(mort_losses, 99.9)

    # Conditional VaR/ES (given a loss occurs) — the tail distribution
    nonzero_prop = prop_losses[prop_losses > 0]
    nonzero_mort = mort_losses[mort_losses > 0]

    def cond_var_es(losses, q):
        if len(losses) == 0:
            return 0, 0
        var_val = float(np.percentile(losses, q))
        tail = losses[losses >= var_val]
        es_val = float(np.mean(tail)) if len(tail) > 0 else var_val
        return round(var_val, 2), round(es_val, 2)

    cprop_var_95, cprop_es_95 = cond_var_es(nonzero_prop, 95)
    cprop_var_999, cprop_es_999 = cond_var_es(nonzero_prop, 99.9)
    cmort_var_95, cmort_es_95 = cond_var_es(nonzero_mort, 95)
    cmort_var_999, cmort_es_999 = cond_var_es(nonzero_mort, 99.9)

    from models.audit import log_model_usage
    log_model_usage("risk_analytics", "portfolio_var", parameters={
        "num_properties": len(prop_values),
        "num_storms": n_storms,
        "var_95": prop_var_95,
        "es_95": prop_es_95,
        "var_999": prop_var_999,
    }, context="Portfolio VaR computation", source="api")

    # Probability of any loss
    prob_loss = round(len(nonzero_prop) / n_storms * 100, 4) if n_storms > 0 else 0

    # Build histogram bins for the chart (property damage distribution)
    # Focus on non-zero tail for detail
    nonzero_prop = prop_losses[prop_losses > 0]
    n_nonzero = len(nonzero_prop)

    # Histogram: 50 bins from 0 to max
    max_loss = float(np.max(prop_losses)) if n_nonzero > 0 else 0
    n_bins = 50
    bin_width = max_loss / n_bins if max_loss > 0 else 1
    hist_bins = []
    for b in range(n_bins):
        lo = b * bin_width
        hi = (b + 1) * bin_width
        count = int(np.sum((prop_losses > lo) & (prop_losses <= hi)))
        hist_bins.append({
            'lo': round(lo, 2),
            'hi': round(hi, 2),
            'count': count,
        })

    # Mortgage impairment histogram
    nonzero_mort = mort_losses[mort_losses > 0]
    max_mort = float(np.max(mort_losses)) if len(nonzero_mort) > 0 else 0
    mort_bin_width = max_mort / n_bins if max_mort > 0 else 1
    mort_hist_bins = []
    for b in range(n_bins):
        lo = b * mort_bin_width
        hi = (b + 1) * mort_bin_width
        count = int(np.sum((mort_losses > lo) & (mort_losses <= hi)))
        mort_hist_bins.append({
            'lo': round(lo, 2),
            'hi': round(hi, 2),
            'count': count,
        })

    # Count storms at exactly zero
    n_zero = int(np.sum(prop_losses == 0))

    # Top tail storms (for the exceedance detail)
    tail_storms = []
    for sid in all_storm_ids:
        if sid in storm_data:
            d = storm_data[sid]
            tail_storms.append({
                'storm_id': sid,
                'property_damage': round(d['property_damage'], 2),
                'mortgage_impairment': round(d['mortgage_impairment'], 2),
                'n_affected': d['n_affected'],
            })
    tail_storms.sort(key=lambda s: s['property_damage'], reverse=True)

    return jsonify({
        'status': 'success',
        'storm_count': n_storms,
        'storms_with_damage': n_nonzero,
        'storms_zero_damage': n_zero,
        'prob_loss_pct': prob_loss,
        'total_portfolio_value': round(total_portfolio_value, 2),
        'total_portfolio_mortgages': round(total_portfolio_mortgages, 2),
        'property_damage': {
            'mean': round(float(np.mean(prop_losses)), 2),
            'std': round(float(np.std(prop_losses)), 2),
            'var_95': prop_var_95,
            'var_999': prop_var_999,
            'es_95': prop_es_95,
            'es_999': prop_es_999,
            'max': round(float(np.max(prop_losses)), 2),
            'cond_mean': round(float(np.mean(nonzero_prop)), 2) if len(nonzero_prop) > 0 else 0,
            'cond_var_95': cprop_var_95,
            'cond_var_999': cprop_var_999,
            'cond_es_95': cprop_es_95,
            'cond_es_999': cprop_es_999,
        },
        'mortgage_impairment': {
            'mean': round(float(np.mean(mort_losses)), 2),
            'std': round(float(np.std(mort_losses)), 2),
            'var_95': mort_var_95,
            'var_999': mort_var_999,
            'es_95': mort_es_95,
            'es_999': mort_es_999,
            'max': round(float(np.max(mort_losses)), 2),
            'cond_mean': round(float(np.mean(nonzero_mort)), 2) if len(nonzero_mort) > 0 else 0,
            'cond_var_95': cmort_var_95,
            'cond_var_999': cmort_var_999,
            'cond_es_95': cmort_es_95,
            'cond_es_999': cmort_es_999,
        },
        'prop_histogram': hist_bins,
        'mort_histogram': mort_hist_bins,
        'tail_storms': tail_storms[:50],
    })
