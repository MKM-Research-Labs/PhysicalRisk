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

"""Test-to-model mapping and model metadata."""

# Maps test file paths (relative to project root) to model IDs.
# Updated to reflect modular test structure (no test_ prefix).
TEST_MODEL_MAP = {
    # ---------------------------------------------------------------------------
    # MKM-GH-001  GEV Hazard Model
    # ---------------------------------------------------------------------------
    'tests/port/hazard/hazard_builder.py':              'MKM-GH-001',

    # ---------------------------------------------------------------------------
    # MKM-SI-001  Storm Intensity Distribution
    # ---------------------------------------------------------------------------
    'tests/models/intensity/distribution.py':           'MKM-SI-001',
    'tests/port/storm/storm_generator.py':              'MKM-SI-001',
    'tests/port/storm/storm_duration.py':               'MKM-SI-001',
    'tests/port/storm/storm_gap.py':                    'MKM-SI-001',
    'tests/port/storm/storm_sequence.py':               'MKM-SI-001',

    # ---------------------------------------------------------------------------
    # MKM-SG-001  Storm-Gauge Response Model
    # ---------------------------------------------------------------------------
    'tests/models/stormgauge/forward_model.py':         'MKM-SG-001',
    'tests/port/gauge/gauge_generator.py':              'MKM-SG-001',
    'tests/port/gauge/rand_gauge.py':                   'MKM-SG-001',

    # ---------------------------------------------------------------------------
    # MKM-PR-001  PRS Pricing Model
    # ---------------------------------------------------------------------------
    'tests/models/prs/prs_pricing.py':                  'MKM-PR-001',
    'tests/port/propertyhc/basis.py':                   'MKM-PR-001',
    'tests/port/propertyhc/generator.py':               'MKM-PR-001',
    'tests/port/propertyhc/pricing.py':                 'MKM-PR-001',
    'tests/models/schedule/maturity.py':                'MKM-PR-001',

    # ---------------------------------------------------------------------------
    # MKM-PV-001  Property Valuation
    # ---------------------------------------------------------------------------
    'tests/port/property/property_generator.py':        'MKM-PV-001',
    'tests/port/property/rand_property_mortgage.py':    'MKM-PV-001',

    # ---------------------------------------------------------------------------
    # MKM-MP-001  Mortgage Pricer
    # ---------------------------------------------------------------------------
    'tests/port/mortgage/mortgage_generator.py':        'MKM-MP-001',
    'tests/models/mortgage/credit.py':                  'MKM-MP-001',
    'tests/models/mortgage/payment.py':                 'MKM-MP-001',
    'tests/models/mortgage/pricing.py':                 'MKM-MP-001',

    # ---------------------------------------------------------------------------
    # MKM-DD-001  Flood Risk (Depth-Damage / Velocity)
    # ---------------------------------------------------------------------------
    'tests/models/velocity.py':                         'MKM-DD-001',
    'tests/models/risk/risk_assessor.py':               'MKM-DD-001',
    'tests/models/floodrisk/risk_visualization.py':     'MKM-DD-001',

    # ---------------------------------------------------------------------------
    # MKM-SS-001  Storm Sequence Generator
    # ---------------------------------------------------------------------------
    'tests/port/storm/sequence_gen.py':                 'MKM-SS-001',
    'tests/port/storm/batch_generator.py':              'MKM-SS-001',
    'tests/port/storm/stressm.py':                      'MKM-SS-001',

    # ---------------------------------------------------------------------------
    # MKM-FC-001  Flood Probability Classifier
    # ---------------------------------------------------------------------------
    'tests/port/stress/classifier.py':                  'MKM-FC-001',
    'tests/port/stress/hydrograph.py':                  'MKM-FC-001',
    'tests/port/stress/labels.py':                      'MKM-FC-001',
    'tests/port/stress/sampling.py':                    'MKM-FC-001',
    'tests/port/stress/storms_file.py':                 'MKM-FC-001',
    'tests/routes/trading/stress_routes.py':            'MKM-FC-001',
    'tests/routes/trading/port_stress_routes.py':       'MKM-FC-001',

    # ---------------------------------------------------------------------------
    # MKM-TD-001  Trading Desk (Delta Engine, P&L, EOD, Blotter)
    # ---------------------------------------------------------------------------
    'tests/models/trading/delta/engine.py':             'MKM-TD-001',
    'tests/models/trading/delta/formulas.py':           'MKM-TD-001',
    'tests/models/trading/pnl/daily_pnl.py':            'MKM-TD-001',
    'tests/models/trading/pnl/eod.py':                  'MKM-TD-001',
    'tests/models/trading/pnl/marks.py':                'MKM-TD-001',
    'tests/models/trading/book/leg_pvs.py':             'MKM-TD-001',
    'tests/models/trading/book/market_making.py':       'MKM-TD-001',
    'tests/models/trading/book/thames_central.py':      'MKM-TD-001',
    'tests/models/trading/historical_eod.py':           'MKM-TD-001',
    'tests/models/trading/market_state.py':             'MKM-TD-001',
    'tests/models/trading/stress_hydrograph.py':        'MKM-TD-001',
    'tests/routes/trading/blotter_routes.py':           'MKM-TD-001',
    'tests/routes/trading/curves_routes.py':            'MKM-TD-001',
    'tests/routes/trading/eod_routes.py':               'MKM-TD-001',
    'tests/routes/trading/market_state_routes.py':      'MKM-TD-001',
    'tests/routes/trading/risk_routes.py':              'MKM-TD-001',
    'tests/visual/trading/blotter_detail.py':           'MKM-TD-001',
    'tests/visual/trading/eod_detail.py':               'MKM-TD-001',
    'tests/visual/trading/market_detail.py':            'MKM-TD-001',

    # ---------------------------------------------------------------------------
    # CDM-ALL  CDM Schema Validation
    # ---------------------------------------------------------------------------
    'tests/port/cdm/schemas.py':                        'CDM-ALL',
    'tests/port/cdm/schema_basics.py':                  'CDM-ALL',
    'tests/port/cdm/gauge_mapping.py':                  'CDM-ALL',
    'tests/port/cdm/property_mapping.py':               'CDM-ALL',
    'tests/port/cdm/mortgage_mapping.py':               'CDM-ALL',
    'tests/port/cdm/cdm_all.py':                        'CDM-ALL',
}

MODEL_INFO = {
    'MKM-SI-001': {'name': 'Storm Intensity Distribution',      'dir': 'storm_intensity'},
    'MKM-SG-001': {'name': 'Storm-Gauge Response Model',        'dir': 'storm_gauge'},
    'MKM-GH-001': {'name': 'GEV Hazard Model',                  'dir': 'gev_hazard'},
    'MKM-PR-001': {'name': 'PRS Pricing Model',                 'dir': 'prs_pricing'},
    'MKM-DD-001': {'name': 'Flood Risk (Depth-Damage)',         'dir': 'flood_risk'},
    'MKM-SP-001': {'name': 'Spatial Interpolation',             'dir': None},
    'MKM-PV-001': {'name': 'Property Valuation',                'dir': 'property_valuation'},
    'MKM-IP-001': {'name': 'Insurance Premium',                 'dir': None},
    'MKM-MP-001': {'name': 'Mortgage Pricer',                   'dir': 'mortgage_pricer'},
    'MKM-RA-001': {'name': 'Risk Analytics',                    'dir': 'risk_assessment'},
    'MKM-FC-001': {'name': 'Flood Probability Classifier',      'dir': 'flood_classifier'},
    'MKM-SS-001': {'name': 'Storm Sequence Generator',          'dir': 'storm_multi'},
    'MKM-TD-001': {'name': 'Trading Desk',                      'dir': None},
    'CDM-ALL':    {'name': 'CDM Schema Validation',             'dir': None},
    'PLATFORM':   {'name': 'Platform Infrastructure',           'dir': None},
}

# Short alias -> full model ID for --model flag
MODEL_ALIASES = {
    'SI': 'MKM-SI-001', 'SG': 'MKM-SG-001', 'GH': 'MKM-GH-001',
    'PR': 'MKM-PR-001', 'DD': 'MKM-DD-001', 'SP': 'MKM-SP-001',
    'PV': 'MKM-PV-001', 'IP': 'MKM-IP-001', 'MP': 'MKM-MP-001',
    'RA': 'MKM-RA-001', 'FC': 'MKM-FC-001', 'SS': 'MKM-SS-001', 'TD': 'MKM-TD-001',
}
