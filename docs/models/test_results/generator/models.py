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

"""Test-to-model attribution rules and model metadata."""

# Rules attributing test files (relative to project root) to model IDs.
#
# A rule ending in '/' claims that directory and everything beneath it; any
# other rule is a glob matched against file names in exactly that directory,
# never across it. Resolution is most-specific-first — file glob over directory
# prefix, longer prefix over shorter — so the order below is for reading only.
# See attribution.py for the resolver and the reconciliation that keeps these
# rules honest.
#
# Prefer the glob form ('genesis*.py') over naming one file: splitting an
# oversized test module into _part1/_part2 is routine here, and under the exact
# paths this list used to hold, every such split silently cost a model its test
# evidence.
TEST_MODEL_RULES = [
    # ---------------------------------------------------------------------------
    # MKM-GH-001  GEV Hazard Model
    # ---------------------------------------------------------------------------
    ('tests/port/hazard/hazard_builder*.py',            'MKM-GH-001'),

    # ---------------------------------------------------------------------------
    # MKM-SI-001  Storm Intensity Distribution
    # ---------------------------------------------------------------------------
    # 'tests/port/storm/storm_generator.py' is gone from this list: no file of
    # that name has ever existed in the tree. tests/port/storm/storm_intensity.py
    # is the obvious candidate but has never been attributed, so claiming it here
    # would be a change of evidence, not a repair.
    ('tests/models/intensity/distribution*.py',         'MKM-SI-001'),
    ('tests/port/storm/storm_duration*.py',             'MKM-SI-001'),
    ('tests/port/storm/storm_gap*.py',                  'MKM-SI-001'),
    ('tests/port/storm/storm_sequence*.py',             'MKM-SI-001'),

    # ---------------------------------------------------------------------------
    # MKM-SG-001  Storm-Gauge Response Model
    # ---------------------------------------------------------------------------
    ('tests/models/stormgauge/forward_model*.py',       'MKM-SG-001'),
    ('tests/port/gauge/gauge_generator*.py',            'MKM-SG-001'),
    ('tests/port/gauge/rand_gauge*.py',                 'MKM-SG-001'),

    # ---------------------------------------------------------------------------
    # MKM-PR-001  PRS Pricing Model
    # ---------------------------------------------------------------------------
    ('tests/models/prs/prs_pricing*.py',                'MKM-PR-001'),
    ('tests/port/propertyhc/basis*.py',                 'MKM-PR-001'),
    ('tests/port/propertyhc/generator*.py',             'MKM-PR-001'),
    ('tests/port/propertyhc/pricing*.py',               'MKM-PR-001'),
    ('tests/models/schedule/',                          'MKM-PR-001'),

    # ---------------------------------------------------------------------------
    # MKM-PV-001  Property Valuation
    # ---------------------------------------------------------------------------
    ('tests/port/property/property_generator*.py',      'MKM-PV-001'),
    ('tests/port/property/rand_property_mortgage*.py',  'MKM-PV-001'),

    # ---------------------------------------------------------------------------
    # MKM-MP-001  Mortgage Pricer
    # ---------------------------------------------------------------------------
    # tests/models/mortgage/ became tests/models/loan/ when the shared pricing
    # engine was renamed MortgagePricer -> LoanPricer (eac21032); credit.py,
    # payment.py and pricing.py moved with it and gained the test_ prefix.
    ('tests/port/mortgage/mortgage_generator*.py',      'MKM-MP-001'),
    ('tests/models/loan/',                              'MKM-MP-001'),

    # ---------------------------------------------------------------------------
    # MKM-DD-001  Flood Risk (Depth-Damage / Velocity)
    # ---------------------------------------------------------------------------
    ('tests/models/velocity*.py',                       'MKM-DD-001'),
    ('tests/models/floodrisk/risk_visualization*.py',   'MKM-DD-001'),

    # ---------------------------------------------------------------------------
    # MKM-SS-001  Storm Sequence Generator
    # ---------------------------------------------------------------------------
    # 'tests/port/storm/stressm.py' is gone from this list: no such file has
    # ever existed. tests/port/storm/stressm/ is a directory, and it belongs to
    # the Stress Test Pipeline (MKM-ST-001) below.
    ('tests/port/storm/sequence_gen*.py',               'MKM-SS-001'),
    ('tests/port/storm/batch_generator*.py',            'MKM-SS-001'),

    # ---------------------------------------------------------------------------
    # MKM-FPO-001  Flood Polynomial Model
    # ---------------------------------------------------------------------------
    ('tests/models/stress/flood_poly*.py',              'MKM-FPO-001'),

    # ---------------------------------------------------------------------------
    # MKM-FC-001  Flood Probability Classifier
    # ---------------------------------------------------------------------------
    # The tests/port/stress/* paths this model used to name were removed from the
    # tree; its tests live beside the model, and exercise the flood_classifier
    # package directly (models.stress.flood_classifier._predictor).
    ('tests/models/stress/flood_classifier*.py',        'MKM-FC-001'),
    ('tests/models/stress/test_flood_predictor_coverage*.py', 'MKM-FC-001'),
    ('tests/routes/trading/test_classifiers_*.py',      'MKM-FC-001'),

    # ---------------------------------------------------------------------------
    # MKM-DE-001  Delta Engine
    # ---------------------------------------------------------------------------
    # Its own inventory model rather than part of the Trading Desk aggregate:
    # these exercise models.trading.delta_engine.engine directly.
    ('tests/models/trading/delta/',                     'MKM-DE-001'),

    # ---------------------------------------------------------------------------
    # MKM-TD-001  Trading Desk (P&L, EOD, Blotter)
    # ---------------------------------------------------------------------------
    # 'tests/models/trading/historical_eod.py' never existed; the EOD history
    # tests live in tests/port/historical_eod/, which is claimed here.
    ('tests/models/trading/pnl/daily_pnl*.py',          'MKM-TD-001'),
    ('tests/models/trading/pnl/eod*.py',                'MKM-TD-001'),
    ('tests/models/trading/pnl/marks*.py',              'MKM-TD-001'),
    ('tests/models/trading/book/',                      'MKM-TD-001'),
    ('tests/models/trading/market_state*.py',           'MKM-TD-001'),
    ('tests/models/trading/stress_hydrograph*.py',      'MKM-TD-001'),
    ('tests/port/historical_eod/',                      'MKM-TD-001'),
    ('tests/routes/trading/blotter_routes*.py',         'MKM-TD-001'),
    ('tests/routes/trading/curves_routes*.py',          'MKM-TD-001'),
    ('tests/routes/trading/eod_routes*.py',             'MKM-TD-001'),
    ('tests/routes/trading/market_state_routes*.py',    'MKM-TD-001'),
    ('tests/routes/trading/risk_routes*.py',            'MKM-TD-001'),
    ('tests/visual/trading/blotter_detail*.py',         'MKM-TD-001'),
    ('tests/visual/trading/eod_detail*.py',             'MKM-TD-001'),
    ('tests/visual/trading/market_detail*.py',          'MKM-TD-001'),

    # ---------------------------------------------------------------------------
    # MKM-RA-001  Risk Analytics
    # ---------------------------------------------------------------------------
    ('tests/models/floodrisk/risk_analytics*.py',       'MKM-RA-001'),

    # ---------------------------------------------------------------------------
    # MKM-SP-001  Spatial Interpolation
    # ---------------------------------------------------------------------------
    ('tests/models/floodrisk/spatial*.py',              'MKM-SP-001'),
    ('tests/models/floodrisk/test_spatial_coverage*.py', 'MKM-SP-001'),

    # ---------------------------------------------------------------------------
    # MKM-IP-001  Insurance Premium
    # ---------------------------------------------------------------------------
    ('tests/models/valuation/insurance*.py',            'MKM-IP-001'),

    # ---------------------------------------------------------------------------
    # MKM-GHD-001  GaugeHD Synthetic
    # ---------------------------------------------------------------------------
    ('tests/models/synthetic*.py',                      'MKM-GHD-001'),
    ('tests/models/hazard/test_synthetic_coverage*.py', 'MKM-GHD-001'),
    ('tests/port/gauge/test_synthetic_gauge*.py',       'MKM-GHD-001'),
    ('tests/port/gauge/test_gaugehd_runner*.py',        'MKM-GHD-001'),
    ('tests/port/gauge/test_gaugehd_module*.py',        'MKM-GHD-001'),

    # ---------------------------------------------------------------------------
    # MKM-ST-001  Stress Test Pipeline
    # ---------------------------------------------------------------------------
    ('tests/port/storm/stressm/test_batch_train*.py',   'MKM-ST-001'),
    ('tests/port/storm/stressm/test_generate*.py',      'MKM-ST-001'),
    ('tests/port/storm/stressm/test_records*.py',       'MKM-ST-001'),
    ('tests/port/storm/stressm/test_single_gauge*.py',  'MKM-ST-001'),
    ('tests/port/storm/stressm/test_gauge_parser*.py',  'MKM-ST-001'),
    ('tests/port/storm/stressm/test_helpers*.py',       'MKM-ST-001'),
    ('tests/port/storm/stressm/test_pipeline_coverage*.py', 'MKM-ST-001'),
    ('tests/port/storm/stressm/test_classifier*.py',    'MKM-ST-001'),

    # ---------------------------------------------------------------------------
    # MKM-PF-001  Property Flood Response
    # ---------------------------------------------------------------------------
    ('tests/models/risk/',                              'MKM-PF-001'),

    # ---------------------------------------------------------------------------
    # MKM-BRI-001  Building Resilience Index Model
    # ---------------------------------------------------------------------------
    ('tests/port/cdm/test_bri_helper*.py',              'MKM-BRI-001'),
    ('tests/port/cdm/test_bri_aggregation*.py',         'MKM-BRI-001'),
    ('tests/port/cdm/test_resilience_generator*.py',    'MKM-BRI-001'),
    ('tests/port/cdm/test_consistency_fixes*.py',       'MKM-BRI-001'),
    ('tests/port/cdm/test_schema_invariants*.py',       'MKM-BRI-001'),
    ('tests/port/cdm/test_flood_resilience_model*.py',  'MKM-BRI-001'),

    # ---------------------------------------------------------------------------
    # MKM-BRF-001  BRI-Adjusted Floor Level Model
    # ---------------------------------------------------------------------------
    ('tests/models/floodrisk/test_bri_floor_level*.py', 'MKM-BRF-001'),

    # ---------------------------------------------------------------------------
    # MKM-FIRE-001  Building Fire-Resilience Credit Model
    # ---------------------------------------------------------------------------
    ('tests/models/fire/',                              'MKM-FIRE-001'),

    # ---------------------------------------------------------------------------
    # MKM-SEIS-001  Building Seismic-Resilience Credit Model
    # ---------------------------------------------------------------------------
    ('tests/models/seismic/',                           'MKM-SEIS-001'),

    # ---------------------------------------------------------------------------
    # CDM-ALL  CDM Schema Validation
    # ---------------------------------------------------------------------------
    # mortgage_mapping.py was renamed loan_mapping.py in eb98ea84.
    ('tests/port/cdm/schemas*.py',                      'CDM-ALL'),
    ('tests/port/cdm/schema_basics*.py',                'CDM-ALL'),
    ('tests/port/cdm/gauge_mapping*.py',                'CDM-ALL'),
    ('tests/port/cdm/property_mapping*.py',             'CDM-ALL'),
    ('tests/port/cdm/loan_mapping*.py',                 'CDM-ALL'),
    ('tests/port/cdm/cdm_all*.py',                      'CDM-ALL'),

    # ---------------------------------------------------------------------------
    # MKM-TC-001  Tropical Cyclone Progression and Wind-Field
    # ---------------------------------------------------------------------------
    ('tests/config/test_typhoon*.py',                   'MKM-TC-001'),
    ('tests/models/typhoon/data_structures*.py',        'MKM-TC-001'),
    ('tests/models/typhoon/genesis*.py',                'MKM-TC-001'),
    ('tests/models/typhoon/transitions*.py',            'MKM-TC-001'),
    ('tests/models/typhoon/particle_filter*.py',        'MKM-TC-001'),
    ('tests/models/typhoon/plausibility*.py',           'MKM-TC-001'),
    ('tests/models/typhoon/import_discipline*.py',      'MKM-TC-001'),
    ('tests/models/typhoon/wind_field/geometry*.py',    'MKM-TC-001'),
    ('tests/models/typhoon/wind_field/radial*.py',      'MKM-TC-001'),
    ('tests/models/typhoon/wind_field/asymmetry*.py',   'MKM-TC-001'),
    ('tests/models/typhoon/wind_field/surface*.py',     'MKM-TC-001'),
    ('tests/models/typhoon/wind_field/point*.py',       'MKM-TC-001'),
    ('tests/models/typhoon/wind_field/time_series*.py', 'MKM-TC-001'),
    ('tests/models/typhoon/wind_field/windfield_class*.py', 'MKM-TC-001'),
    ('tests/models/typhoon/pipeline/',                  'MKM-TC-001'),
    ('tests/catch/halong/test_tc*.py',                  'MKM-TC-001'),

    # ---------------------------------------------------------------------------
    # MKM-WS-001  Event Wind Lookup (wind-at-point query)
    # ---------------------------------------------------------------------------
    ('tests/models/windspeed/',                         'MKM-WS-001'),

    # ---------------------------------------------------------------------------
    # MKM-WD-001  Wind Damage
    # ---------------------------------------------------------------------------
    ('tests/models/winddamage/',                        'MKM-WD-001'),
]

MODEL_INFO = {
    'MKM-SI-001': {'name': 'Storm Intensity Distribution',      'dir': 'storm_intensity'},
    'MKM-SG-001': {'name': 'Storm-Gauge Response Model',        'dir': 'storm_gauge'},
    'MKM-GH-001': {'name': 'GEV Hazard Model',                  'dir': 'gev_hazard'},
    'MKM-PR-001': {'name': 'PRS Pricing Model',                 'dir': 'prs_pricing'},
    'MKM-DD-001': {'name': 'Flood Risk (Depth-Damage)',         'dir': 'flood_risk'},
    'MKM-SP-001': {'name': 'Spatial Interpolation',             'dir': 'spatial_model'},
    'MKM-PV-001': {'name': 'Property Valuation',                'dir': 'property_valuation'},
    'MKM-IP-001': {'name': 'Insurance Premium',                 'dir': 'insurance_premium'},
    'MKM-MP-001': {'name': 'Mortgage Pricer',                   'dir': 'mortgage_pricer'},
    'MKM-RA-001': {'name': 'Risk Analytics',                    'dir': 'risk_assessment'},
    'MKM-FC-001': {'name': 'Flood Probability Classifier',      'dir': 'flood_classifier'},
    'MKM-SS-001': {'name': 'Storm Sequence Generator',          'dir': 'storm_multi'},
    'MKM-GHD-001': {'name': 'GaugeHD Synthetic',                'dir': 'gaugehd_synthetic'},
    'MKM-ST-001': {'name': 'Stress Test Pipeline',              'dir': 'stressm_pipeline'},
    'MKM-PF-001': {'name': 'Property Flood Response',           'dir': 'property_flood_response'},
    'MKM-FPO-001': {'name': 'Flood Polynomial Model',            'dir': 'flood_poly'},
    'MKM-DE-001': {'name': 'Delta Engine',                      'dir': 'delta_engine'},
    'MKM-BRI-001': {'name': 'Building Resilience Index Model',  'dir': 'bri_resilience'},
    'MKM-BRF-001': {'name': 'BRI-Adjusted Floor Level Model',   'dir': 'bri_floor'},
    'MKM-TC-001': {'name': 'Tropical Cyclone Progression and Wind-Field', 'dir': 'typhoon'},
    'MKM-WS-001': {'name': 'Event Wind Lookup',                 'dir': 'wind_speed'},
    'MKM-WD-001': {'name': 'Wind Damage',                       'dir': 'wind_damage'},
    'MKM-FIRE-001': {'name': 'Building Fire-Resilience Credit Model',
                     'dir': 'fire_resilience'},
    'MKM-SEIS-001': {'name': 'Building Seismic-Resilience Credit Model',
                     'dir': 'seismic_resilience'},
    'MKM-TD-001': {'name': 'Trading Desk',                      'dir': 'trading_desk'},
    'CDM-ALL':    {'name': 'CDM Schema Validation',             'dir': 'cdm_schema'},
    'E2E-ALL':    {'name': 'End-to-End Browser Tests',          'dir': None},
    'PLATFORM':   {'name': 'Platform Infrastructure',           'dir': None},
}

# Short alias -> full model ID for --model flag
MODEL_ALIASES = {
    'SI': 'MKM-SI-001', 'SG': 'MKM-SG-001', 'GH': 'MKM-GH-001',
    'PR': 'MKM-PR-001', 'DD': 'MKM-DD-001', 'SP': 'MKM-SP-001',
    'PV': 'MKM-PV-001', 'IP': 'MKM-IP-001', 'MP': 'MKM-MP-001',
    'RA': 'MKM-RA-001', 'FC': 'MKM-FC-001', 'SS': 'MKM-SS-001', 'TD': 'MKM-TD-001',
    'GHD': 'MKM-GHD-001', 'ST': 'MKM-ST-001', 'PF': 'MKM-PF-001',
    'DE': 'MKM-DE-001', 'FPO': 'MKM-FPO-001',
    'BRI': 'MKM-BRI-001',
    'BRF': 'MKM-BRF-001',
    'TC': 'MKM-TC-001',
    'WS': 'MKM-WS-001',
    'WD': 'MKM-WD-001',
    'FIRE': 'MKM-FIRE-001',
    'SEIS': 'MKM-SEIS-001',
    'E2E': 'E2E-ALL',
}
