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

"""Curated parameter data for the model parameter inventory."""


def get_parameter_sections():
    """Return all parameter sections for the inventory.

    Each section is a dict with:
      - title: Section heading
      - model_id: Governance model ID
      - source: Primary source file(s)
      - subsections: list of (subsection_title, params_list)
        where each param is (name, value, description, source_ref)
    """
    return [
        # ──────────────────────────────────────────────
        # 1. PRS PRICING (Analytical)
        # ──────────────────────────────────────────────
        {
            'title': 'PRS Pricing --- Analytical Model',
            'model_id': 'MKM-PR-001',
            'source': 'models/hazard/prs_analytical.py',
            'subsections': [
                ('Basis Waterfall Components', [
                    ('MODEL_UNCERTAINTY_BPS', '2.0', 'Fixed model uncertainty spread (basis points)', 'hazard/prs_analytical.py:20'),
                    ('DISTANCE_RATE_BPS_PER_KM', '0.5', 'Distance basis rate per km', 'hazard/prs_analytical.py:46'),
                    ('DISTANCE_MAX_BPS', '6.0', 'Distance basis cap (bps)', 'hazard/prs_analytical.py:47'),
                    ('DISTANCE_CAP_KM', '12.0', 'Maximum distance for basis', 'hazard/prs_analytical.py:48'),
                    ('ELEVATION_RATE_BPS_PER_M', '0.2', 'Elevation benefit rate per metre', 'hazard/prs_analytical.py:51'),
                    ('ELEVATION_MAX_BENEFIT_BPS', '3.0', 'Maximum elevation benefit cap (bps)', 'hazard/prs_analytical.py:52'),
                    ('MIN_PRS_SPREAD_BPS', '2.0', 'Minimum PRS spread floor (bps)', 'hazard/prs_analytical.py:62'),
                    ('CONSTRUCTION_YEAR_CUTOFF', '2000', 'Pre-cutoff adds 1.0 bps penalty', 'hazard/prs_analytical.py:43'),
                ]),
                ('Terrain Basis by EA Flood Zone (bps)', [
                    ('Zone 3b / 3a / 3', '3.0', 'High flood risk zones', 'hazard/prs_analytical.py:23-30'),
                    ('Zone 2', '2.0', 'Medium flood risk zone', 'hazard/prs_analytical.py:23-30'),
                    ('Zone 1', '0.0', 'Low flood risk zone', 'hazard/prs_analytical.py:23-30'),
                    ('Enhanced Defence', '-1.0', 'Protected area benefit', 'hazard/prs_analytical.py:23-30'),
                ]),
                ('Composition Basis by Property Type (bps)', [
                    ('Flat', '2.0', 'Higher risk construction type', 'hazard/prs_analytical.py:33-40'),
                    ('Bungalow', '1.0', 'Ground-floor exposure', 'hazard/prs_analytical.py:33-40'),
                    ('Terraces', '0.5', 'Moderate exposure', 'hazard/prs_analytical.py:33-40'),
                    ('Semi-detached / Detached', '0.0', 'Base case', 'hazard/prs_analytical.py:33-40'),
                ]),
                ('Recovery Rates by Trigger', [
                    ('any_flood (> 0m)', '0.85', 'Recovery rate for any flood trigger', 'hazard/prs_analytical.py:55-59'),
                    ('moderate (> 0.5m)', '0.70', 'Recovery rate for moderate flood', 'hazard/prs_analytical.py:55-59'),
                    ('severe (> 1.0m)', '0.50', 'Recovery rate for severe flood', 'hazard/prs_analytical.py:55-59'),
                ]),
                ('CDS Pricing', [
                    ('dt', '0.25', 'Quarterly period length (years)', 'hazard/prs_analytical.py:97'),
                    ('max_annual_hazard_rate', '0.999', 'Cap for continuous hazard rate', 'hazard/prs_analytical.py:95'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 2. PRS PRICING (QuantLib)
        # ──────────────────────────────────────────────
        {
            'title': 'PRS Pricing --- QuantLib CDS',
            'model_id': 'MKM-PR-001',
            'source': 'models/prshc.py',
            'subsections': [
                ('Default Trade Parameters', [
                    ('notional', '10,000,000', 'Default notional (GBP)', 'prshc.py:131'),
                    ('tenor_years', '5', 'Default swap tenor', 'prshc.py:132'),
                    ('running_spread', '0.01', 'Default running spread (100 bps)', 'prshc.py:133'),
                    ('recovery_rate', '0.0', 'Default recovery (no recovery for flood)', 'prshc.py:134'),
                    ('risk_free_rate', '0.03', 'Default risk-free rate (3\\%)', 'prshc.py:135'),
                    ('implied_hazard_rate fallback', '0.05', 'Fallback hazard rate (5\\%)', 'prshc.py:83'),
                ]),
                ('QuantLib Conventions', [
                    ('Schedule frequency', 'Quarterly', 'CDS payment frequency', 'prshc.py:194'),
                    ('Calendar', 'TARGET()', 'TARGET settlement calendar', 'prshc.py:182'),
                    ('Day counter', 'Actual/360', 'Accrual day count convention', 'prshc.py:184'),
                    ('Business day convention', 'Following', 'Roll convention', 'prshc.py:183'),
                    ('Date generation rule', 'TwentiethIMM', 'IMM date schedule', 'prshc.py:198'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 3. GEV HAZARD
        # ──────────────────────────────────────────────
        {
            'title': 'GEV Hazard Curve Model',
            'model_id': 'MKM-GH-001',
            'source': 'models/hazard/gev.py, models/hazard/builder.py',
            'subsections': [
                ('Hazard Curve Construction', [
                    ('STANDARD_THRESHOLDS', '[0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]', 'Flood depth thresholds (m)', 'hazard/builder.py:24'),
                    ('RETURN_PERIODS', '[2, 5, 10, 20, 50, 100]', 'Standard return periods (years)', 'hazard/builder.py:25'),
                    ('exceedance_prob floor', '0.01', 'Floor at 1\\% (100-yr return period)', 'hazard/builder.py:69-70'),
                ]),
                ('Term Structure', [
                    ('max_years', '5', 'Maximum years for term structure', 'hazard/gev.py:48'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 4. STORM-GAUGE RESPONSE
        # ──────────────────────────────────────────────
        {
            'title': 'Storm-Gauge Response Model',
            'model_id': 'MKM-SG-001',
            'source': 'models/hazard/response_model.py, models/stormgauge/forward_model.py',
            'subsections': [
                ('Gauge Alert Thresholds (defaults)', [
                    ('flood_alert', '3.0', 'Flood alert level (m)', 'hazard/response_model.py:42'),
                    ('flood_warning', '4.0', 'Flood warning level (m)', 'hazard/response_model.py:43'),
                    ('severe_flood_warning', '5.0', 'Severe warning level (m)', 'hazard/response_model.py:44'),
                ]),
                ('Response Calibration', [
                    ('base_response', 'level_range * 0.015', 'Base gauge response coefficient', 'hazard/response_model.py:59'),
                    ('response_coef variation', 'U(0.8, 1.2)', 'Uniform multiplier on response', 'hazard/response_model.py:60'),
                    ('precip_factor divisor', '35.0', 'Precipitation normalisation (mm)', 'hazard/response_model.py:78'),
                    ('duration_factor cap', '2.0', 'Maximum duration amplification', 'hazard/response_model.py:79'),
                    ('noise factor', 'U(0.85, 1.15)', 'Random noise multiplier', 'hazard/response_model.py:89'),
                ]),
                ('Forward Model --- Spatial Decay', [
                    ('intensity_to_level_scale', '0.1', 'Intensity-to-level conversion scale', 'stormgauge/forward_model.py:42'),
                    ('time_resolution_hours', '0.5', 'Temporal resolution (hours)', 'stormgauge/forward_model.py:43'),
                    ('response_lag_hours', '2.0', 'Lag before gauge response', 'stormgauge/forward_model.py:44'),
                    ('response_decay_hours', '12.0', 'Exponential decay time', 'stormgauge/forward_model.py:45'),
                    ('gamma (intensity mapping)', '0.8', 'Non-linear intensity exponent', 'stormgauge/forward_model.py:195'),
                    ('rise limb multiplier', '3.0', 'Faster rising limb vs decay', 'stormgauge/forward_model.py:244'),
                    ('Earth radius', '6,371 km', 'Haversine distance calculation', 'stormgauge/forward_model.py:54'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 5. STORM INTENSITY
        # ──────────────────────────────────────────────
        {
            'title': 'Storm Intensity Distribution',
            'model_id': 'MKM-SI-001',
            'source': 'models/intensity/distribution.py, models/intensity/parameters.py',
            'subsections': [
                ('Distribution Defaults', [
                    ('base_mean', '45.0', 'Mean storm intensity', 'intensity/distribution.py:33'),
                    ('base_std', '15.0', 'Standard deviation', 'intensity/distribution.py:34'),
                    ('tail_threshold', '60.0', 'Pareto tail crossover point', 'intensity/distribution.py:35'),
                    ('tail_index', '2.5', 'Pareto tail index (heavier = lower)', 'intensity/distribution.py:36'),
                    ('min_intensity', '10.0', 'Minimum storm intensity', 'intensity/distribution.py:37'),
                    ('max_intensity', '100.0', 'Maximum storm intensity', 'intensity/distribution.py:38'),
                ]),
                ('Scenario Families', [
                    ('historical', 'mean=40, std=12, thresh=60, idx=3.0', 'Historical baseline scenario', 'intensity/parameters.py:43-50'),
                    ('baseline', 'mean=45, std=15, thresh=60, idx=2.5', 'Current climate scenario', 'intensity/parameters.py:51-58'),
                    ('moderate_stress', 'mean=50, std=15, thresh=55, idx=2.0', 'Moderate climate stress', 'intensity/parameters.py:59-66'),
                    ('severe_stress', 'mean=55, std=18, thresh=50, idx=1.5', 'Severe climate stress', 'intensity/parameters.py:67-74'),
                    ('extreme', 'mean=60, std=20, thresh=45, idx=1.2', 'Extreme tail scenario', 'intensity/parameters.py:75-79'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 6. FLOOD RISK (Depth-Damage + Velocity)
        # ──────────────────────────────────────────────
        {
            'title': 'Flood Risk --- Depth-Damage and Velocity',
            'model_id': 'MKM-DD-001',
            'source': 'models/floodrisk/depth_damage.py, models/floodrisk/velocity.py',
            'subsections': [
                ('UK Depth-Damage Curve', [
                    ('DEPTH_POINTS', '[0, 0.05, 0.5, 1, 1.5, 2, 3, 4, 5, 6]', 'Flood depth breakpoints (m)', 'floodrisk/depth_damage.py:80'),
                    ('DAMAGE_POINTS', '[0, 0.05, 0.25, 0.4, 0.5, 0.6, 0.75, 0.85, 0.95, 1.0]', 'Damage fraction at each depth', 'floodrisk/depth_damage.py:81'),
                    ('max flood depth', '5.0', 'Maximum modelled depth (m)', 'floodrisk/depth_damage.py:74'),
                    ('max distance', '25,000', 'Maximum distance for damage (m)', 'floodrisk/depth_damage.py:67'),
                ]),
                ('Property Type Factors', [
                    ('residential', '1.0', 'Base case damage factor', 'floodrisk/depth_damage.py:130-134'),
                    ('commercial', '1.2', 'Higher damage for commercial', 'floodrisk/depth_damage.py:130-134'),
                    ('industrial', '0.9', 'Lower damage for industrial', 'floodrisk/depth_damage.py:130-134'),
                ]),
                ('Manning Velocity Model', [
                    ('DEFAULT_ROUGHNESS', '0.04', 'Manning n for urban floodplain', 'floodrisk/velocity.py:15'),
                    ('MIN_SLOPE', '0.001', 'Minimum slope clamp', 'floodrisk/velocity.py:21'),
                    ('DEFAULT_ATTENUATION_LENGTH', '2,000', 'Exponential decay length (m)', 'floodrisk/velocity.py:18'),
                    ('DEFAULT_RECESSION_FACTOR', '1.5', 'Recession limb multiplier', 'floodrisk/velocity.py:24'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 7. SPATIAL INTERPOLATION
        # ──────────────────────────────────────────────
        {
            'title': 'Spatial Interpolation',
            'model_id': 'MKM-SP-001',
            'source': 'models/floodrisk/spatial.py',
            'subsections': [
                ('Spatial Parameters', [
                    ('Earth radius', '6,371,000', 'Haversine radius (m)', 'floodrisk/spatial.py:53'),
                    ('IDW power', '2.0', 'Inverse distance weighting exponent', 'floodrisk/spatial.py:114'),
                    ('IDW min_distance', '1.0', 'Minimum distance floor (m)', 'floodrisk/spatial.py:115'),
                    ('distance_km to degrees', '111.0', 'km per degree latitude', 'floodrisk/spatial.py:40'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 8. RISK ANALYTICS
        # ──────────────────────────────────────────────
        {
            'title': 'Risk Analytics',
            'model_id': 'MKM-RA-001',
            'source': 'models/floodrisk/risk_analytics.py',
            'subsections': [
                ('Monte Carlo Settings', [
                    ('n_simulations', '1,000', 'Default simulation count', 'floodrisk/risk_analytics.py:22'),
                    ('shock_multiplier', '0.2', 'Stress shock (20\\%)', 'floodrisk/risk_analytics.py:54'),
                    ('random_seed', '42', 'Reproducibility seed', 'floodrisk/risk_analytics.py:38'),
                    ('grid_size', '1,000', 'Spatial grid cell size (m)', 'floodrisk/risk_analytics.py:78'),
                ]),
                ('Risk Classification Thresholds', [
                    ('high_risk', '> 0.6', 'Damage ratio for high risk', 'floodrisk/risk_analytics.py:157'),
                    ('medium_risk', '0.3--0.6', 'Damage ratio for medium risk', 'floodrisk/risk_analytics.py:158'),
                    ('low_risk', '0.1--0.3', 'Damage ratio for low risk', 'floodrisk/risk_analytics.py:159'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 9. RISK ASSESSMENT
        # ──────────────────────────────────────────────
        {
            'title': 'Risk Assessment Model',
            'model_id': 'MKM-RA-001',
            'source': 'models/risk/risk_assessor.py',
            'subsections': [
                ('Flood Depth Thresholds', [
                    ('very_low', '0.0 m', 'No flood exposure', 'risk/risk_assessor.py:23-29'),
                    ('low', '0.1 m', 'Minor flooding', 'risk/risk_assessor.py:23-29'),
                    ('medium', '0.5 m', 'Moderate flooding', 'risk/risk_assessor.py:23-29'),
                    ('high', '1.0 m', 'Significant flooding', 'risk/risk_assessor.py:23-29'),
                    ('very_high', '2.0 m', 'Severe flooding', 'risk/risk_assessor.py:23-29'),
                ]),
                ('LTV Risk Thresholds', [
                    ('low', '0.6', 'Low LTV boundary', 'risk/risk_assessor.py:31-36'),
                    ('moderate', '0.8', 'Moderate LTV boundary', 'risk/risk_assessor.py:31-36'),
                    ('high', '0.95', 'High LTV boundary', 'risk/risk_assessor.py:31-36'),
                    ('critical', '1.0', 'Negative equity threshold', 'risk/risk_assessor.py:31-36'),
                ]),
                ('Flood Risk Scores', [
                    ('Very Low', '1', 'Base risk score', 'risk/risk_assessor.py:154-161'),
                    ('Low', '2', '', 'risk/risk_assessor.py:154-161'),
                    ('Medium', '4', '', 'risk/risk_assessor.py:154-161'),
                    ('High', '7', '', 'risk/risk_assessor.py:154-161'),
                    ('Very High', '9', '', 'risk/risk_assessor.py:154-161'),
                    ('Unknown', '3', 'Default when unknown', 'risk/risk_assessor.py:154-161'),
                ]),
                ('LTV Multipliers', [
                    ('> 0.95', '2.0x', 'Near negative equity', 'risk/risk_assessor.py:171-176'),
                    ('> 0.8', '1.5x', 'High LTV', 'risk/risk_assessor.py:171-176'),
                    ('> 0.6', '1.2x', 'Moderate LTV', 'risk/risk_assessor.py:171-176'),
                    ('else', '1.0x', 'Low LTV (base)', 'risk/risk_assessor.py:171-176'),
                ]),
                ('Construction Type Factors', [
                    ('timber / wood', '1.3', 'Highest vulnerability', 'risk/risk_assessor.py:189-197'),
                    ('brick', '1.0', 'Standard', 'risk/risk_assessor.py:189-197'),
                    ('concrete', '0.9', 'More resilient', 'risk/risk_assessor.py:189-197'),
                    ('steel', '0.8', 'Most resilient', 'risk/risk_assessor.py:189-197'),
                ]),
                ('Age Factors', [
                    ('> 100 years', '1.3', 'Heritage property risk', 'risk/risk_assessor.py:181-184'),
                    ('> 50 years', '1.1', 'Older property risk', 'risk/risk_assessor.py:181-184'),
                ]),
                ('Insurance Premium Base Rates', [
                    ('Very Low', '0.001', '0.1\\% of property value', 'risk/risk_assessor.py:391-398'),
                    ('Low', '0.002', '0.2\\%', 'risk/risk_assessor.py:391-398'),
                    ('Medium', '0.005', '0.5\\%', 'risk/risk_assessor.py:391-398'),
                    ('High', '0.015', '1.5\\%', 'risk/risk_assessor.py:391-398'),
                    ('Very High', '0.035', '3.5\\%', 'risk/risk_assessor.py:391-398'),
                    ('Premium cap', '0.10', 'Max 10\\% of property value', 'risk/risk_assessor.py:406'),
                ]),
                ('Distance Risk Factors', [
                    ('<= 0.1 km', '1.0', 'Immediate proximity', 'risk/risk_assessor.py:361-372'),
                    ('<= 0.5 km', '0.8', '', 'risk/risk_assessor.py:361-372'),
                    ('<= 1.0 km', '0.6', '', 'risk/risk_assessor.py:361-372'),
                    ('<= 2.0 km', '0.4', '', 'risk/risk_assessor.py:361-372'),
                    ('<= 5.0 km', '0.2', '', 'risk/risk_assessor.py:361-372'),
                    ('> 5.0 km', '0.1', 'Minimal proximity risk', 'risk/risk_assessor.py:361-372'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 10. PROPERTY VALUATION
        # ──────────────────────────────────────────────
        {
            'title': 'Property Valuation Model',
            'model_id': 'MKM-PV-001',
            'source': 'models/valuation/property_value.py',
            'subsections': [
                ('Floor Area Ranges (sq m)', [
                    ('Flat', '35--120', 'Typical flat range', 'valuation/property_value.py:19-26'),
                    ('Mid-terrace', '60--180', '', 'valuation/property_value.py:19-26'),
                    ('End-terrace', '70--200', '', 'valuation/property_value.py:19-26'),
                    ('Semi-detached', '80--250', '', 'valuation/property_value.py:19-26'),
                    ('Detached', '120--400', '', 'valuation/property_value.py:19-26'),
                    ('Bungalow', '80--200', '', 'valuation/property_value.py:19-26'),
                ]),
                ('Base Price per sqm (GBP)', [
                    ('Detached', '8,000--15,000', 'London market calibration', 'valuation/property_value.py:29-36'),
                    ('Semi-detached', '6,500--12,000', '', 'valuation/property_value.py:29-36'),
                    ('Mid-terrace', '6,000--11,000', '', 'valuation/property_value.py:29-36'),
                    ('End-terrace', '6,200--11,500', '', 'valuation/property_value.py:29-36'),
                    ('Bungalow', '7,000--13,000', '', 'valuation/property_value.py:29-36'),
                    ('Flat', '5,500--10,000', '', 'valuation/property_value.py:29-36'),
                ]),
                ('Age Band Factors (multiplier range)', [
                    ('New build (< 10y)', '1.05--1.15', 'Premium for new', 'valuation/property_value.py:39-45'),
                    ('Modern (10--24y)', '0.95--1.05', 'Near base', 'valuation/property_value.py:39-45'),
                    ('Established (25--49y)', '0.90--1.00', 'Minor discount', 'valuation/property_value.py:39-45'),
                    ('Period (50--99y)', '0.85--0.95', '', 'valuation/property_value.py:39-45'),
                    ('Heritage (100+y)', '0.80--1.20', 'Wide range (character premium)', 'valuation/property_value.py:39-45'),
                ]),
                ('Condition Factors', [
                    ('Excellent', '1.10--1.20', '', 'valuation/property_value.py:48-54'),
                    ('Good', '1.00--1.10', '', 'valuation/property_value.py:48-54'),
                    ('Fair', '0.90--1.00', '', 'valuation/property_value.py:48-54'),
                    ('Poor', '0.70--0.90', '', 'valuation/property_value.py:48-54'),
                    ('Very poor', '0.50--0.70', '', 'valuation/property_value.py:48-54'),
                ]),
                ('Flood Risk Factors', [
                    ('Very Low', '1.00--1.02', 'Near neutral impact', 'valuation/property_value.py:57-63'),
                    ('Low', '0.98--1.00', '', 'valuation/property_value.py:57-63'),
                    ('Medium', '0.92--0.98', '', 'valuation/property_value.py:57-63'),
                    ('High', '0.85--0.92', '', 'valuation/property_value.py:57-63'),
                    ('Very High', '0.75--0.85', 'Significant discount', 'valuation/property_value.py:57-63'),
                ]),
                ('EPC Rating Factors', [
                    ('A', '1.05--1.10', 'Green premium', 'valuation/property_value.py:66-74'),
                    ('B', '1.02--1.05', '', 'valuation/property_value.py:66-74'),
                    ('C', '1.00--1.02', '', 'valuation/property_value.py:66-74'),
                    ('D', '0.98--1.00', '', 'valuation/property_value.py:66-74'),
                    ('E', '0.95--0.98', '', 'valuation/property_value.py:66-74'),
                    ('F', '0.90--0.95', '', 'valuation/property_value.py:66-74'),
                    ('G', '0.85--0.90', 'Energy penalty', 'valuation/property_value.py:66-74'),
                ]),
                ('Valuation Bounds', [
                    ('MIN_PROPERTY_VALUE', '150,000', 'Floor (GBP)', 'valuation/property_value.py:105'),
                    ('MAX_PROPERTY_VALUE', '5,000,000', 'Cap (GBP)', 'valuation/property_value.py:106'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 11. INSURANCE PREMIUM
        # ──────────────────────────────────────────────
        {
            'title': 'Insurance Premium Model',
            'model_id': 'MKM-IP-001',
            'source': 'models/valuation/insurance.py',
            'subsections': [
                ('Property Type Premium Factors', [
                    ('Flat', '0.80--1.00', 'Lower exposure', 'valuation/insurance.py:20-27'),
                    ('Mid-terrace', '0.90--1.10', '', 'valuation/insurance.py:20-27'),
                    ('End-terrace', '1.00--1.20', '', 'valuation/insurance.py:20-27'),
                    ('Semi-detached', '1.10--1.30', '', 'valuation/insurance.py:20-27'),
                    ('Detached', '1.20--1.50', 'Highest exposure', 'valuation/insurance.py:20-27'),
                    ('Bungalow', '1.00--1.20', 'Ground-floor risk', 'valuation/insurance.py:20-27'),
                ]),
                ('Flood Risk Premium Factors', [
                    ('Very Low', '0.90--1.00', '', 'valuation/insurance.py:30-36'),
                    ('Low', '1.00--1.20', '', 'valuation/insurance.py:30-36'),
                    ('Medium', '1.30--1.80', '', 'valuation/insurance.py:30-36'),
                    ('High', '1.80--2.50', '', 'valuation/insurance.py:30-36'),
                    ('Very High', '2.50--4.00', 'Significant loading', 'valuation/insurance.py:30-36'),
                ]),
                ('Premium Bounds', [
                    ('BASE_RATE_RANGE', '1.5--4.0', 'Per GBP 1,000 insured', 'valuation/insurance.py:64'),
                    ('MIN_PREMIUM', '200', 'Floor (GBP)', 'valuation/insurance.py:67'),
                    ('MAX_PREMIUM', '20,000', 'Cap (GBP)', 'valuation/insurance.py:68'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 12. MORTGAGE PRICER
        # ──────────────────────────────────────────────
        {
            'title': 'Mortgage Pricer',
            'model_id': 'MKM-MP-001',
            'source': 'models/mortgage_pricer.py',
            'subsections': [
                ('Credit Spread Schedule', [
                    ('Affordability ratio points', '[0.1, 0.2, ..., 1.0]', '10 interpolation points', 'mortgage_pricer.py:55'),
                    ('Credit spreads', '[50, 100, 200, 300, 500, 800, 1200, 1800, 2500, 3500] bps', 'Corresponding spread curve', 'mortgage_pricer.py:58'),
                    ('Default for zero income', '0.15', '15\\% spread fallback', 'mortgage_pricer.py:141'),
                    ('Minimum spread', '0.001', '10 bps floor', 'mortgage_pricer.py:175'),
                ]),
                ('Flood Risk Multipliers', [
                    ('Very Low', '1.00', 'No adjustment', 'mortgage_pricer.py:178-184'),
                    ('Low', '1.05', '', 'mortgage_pricer.py:178-184'),
                    ('Medium', '1.20', '', 'mortgage_pricer.py:178-184'),
                    ('High', '1.40', '', 'mortgage_pricer.py:178-184'),
                    ('Very High', '1.75', 'Largest loading', 'mortgage_pricer.py:178-184'),
                ]),
                ('LTV Impact Thresholds', [
                    ('> 0.95', '1.5x', 'Near negative equity', 'mortgage_pricer.py:389-396'),
                    ('> 0.9', '1.3x', '', 'mortgage_pricer.py:389-396'),
                    ('> 0.8', '1.1x', '', 'mortgage_pricer.py:389-396'),
                    ('else', '1.0x', 'Low LTV (base)', 'mortgage_pricer.py:389-396'),
                ]),
                ('Default Assumptions', [
                    ('tax_rate', '0.20', 'Corporation tax (20\\%)', 'mortgage_pricer.py:37'),
                    ('gross_annual_income (batch)', '50,000', 'Batch pricing default', 'mortgage_pricer.py:415'),
                    ('interest_rate (batch)', '0.035', '3.5\\% default rate', 'mortgage_pricer.py:417'),
                    ('insurance_rate (batch)', '0.002', '0.2\\% insurance', 'mortgage_pricer.py:418'),
                    ('recovery_haircut (batch)', '0.2', '20\\% recovery haircut', 'mortgage_pricer.py:420'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 13. TIMESERIES STATISTICS
        # ──────────────────────────────────────────────
        {
            'title': 'Timeseries Statistics',
            'model_id': 'MKM-TS-001',
            'source': 'models/statistics/timeseries.py, models/statistics/synthetic.py',
            'subsections': [
                ('Statistical Parameters', [
                    ('days_per_year', '365.25', 'Year length for annual maxima', 'statistics/timeseries.py:48'),
                    ('percentile_bands', '[5, 10, 25, 50, 75, 90, 95, 99]', 'Standard percentile breakpoints', 'statistics/timeseries.py:69-77'),
                ]),
                ('Synthetic Water Level Generation', [
                    ('base_level range', 'U(0.3, 0.5) * flood_alert', 'Normal water level', 'statistics/synthetic.py:62'),
                    ('daily_std', 'base_level * 0.15', 'Daily standard deviation', 'statistics/synthetic.py:63'),
                    ('seasonal_amplitude', 'base_level * 0.25', 'Winter/summer variation', 'statistics/synthetic.py:64'),
                    ('seasonal_peak', 'Day 15 (January)', 'Winter peak offset', 'statistics/synthetic.py:98'),
                    ('minor_flood_prob', '5.0x severe_prob', 'Minor flood frequency', 'statistics/synthetic.py:83'),
                ]),
            ],
        },
        # ──────────────────────────────────────────────
        # 14. FLOOD PROBABILITY CLASSIFIER
        # ──────────────────────────────────────────────
        {
            'title': 'Flood Probability Classifier (GBM)',
            'model_id': 'MKM-FC-001',
            'source': 'models/stress/flood_classifier.py',
            'subsections': [
                ('GBM Hyperparameters', [
                    ('n_estimators', '200', 'Number of boosting rounds', 'stress/flood_classifier.py:76'),
                    ('max_depth', '4', 'Maximum tree depth', 'stress/flood_classifier.py:77'),
                    ('learning_rate', '0.1', 'Shrinkage per round', 'stress/flood_classifier.py:78'),
                    ('subsample', '0.8', 'Row sampling fraction', 'stress/flood_classifier.py:79'),
                    ('min_samples_leaf', '20', 'Minimum leaf node samples', 'stress/flood_classifier.py:80'),
                    ('random_state', '42', 'Random seed for reproducibility', 'stress/flood_classifier.py:81'),
                ]),
                ('Training Configuration', [
                    ('test_size', '0.2', 'Hold-out test fraction (stratified)', 'stress/flood_classifier.py:73'),
                    ('features', '[water_level, hour, delta_w, delta2_w]', 'Four-dimensional feature space (v1.2)', 'stress/flood_classifier.py:55'),
                    ('target', 'flood_flag', 'Binary: 1 if storm breaches alert level', 'stress/flood_classifier.py:56'),
                    ('delta_w', 'w(t) - w(t-1)', 'Velocity: hourly water level change', 'port/src/stress.py'),
                    ('delta2_w', 'dw(t) - dw(t-1)', 'Acceleration: hourly velocity change', 'port/src/stress.py'),
                ]),
                ('Training Noise (upstream)', [
                    ('noise_sigma_start', '0.5 m', 'Gaussian noise std at hour 0', 'port/src/stress.py'),
                    ('noise_sigma_end', '0.1 m', 'Gaussian noise std at hour 167', 'port/src/stress.py'),
                    ('noise_decay', 'Exponential', 'Time-decaying noise envelope', 'port/src/stress.py'),
                    ('num_hours', '168', 'Storm horizon (7 days)', 'port/src/stress.py'),
                ]),
            ],
        },

        # -----------------------------------------------------------------------
        # MKM-SS-001  Storm Sequence Generator
        # -----------------------------------------------------------------------
        {
            'section': 'Storm Sequence Generator (MKM-SS-001)',
            'model_id': 'MKM-SS-001',
            'source': 'port/src/storm_multi/',
            'subsections': [
                ('Event Window', [
                    ('EVENT_WINDOW_HOURS', '168', 'Insurance hours clause event window', 'storm_multi/utils/validation.py'),
                    ('MIN_DRAINAGE_WINDOW_HOURS', '12', 'Minimum post-precipitation drainage window', 'storm_multi/utils/validation.py'),
                    ('MAX_PRECIP_END_HOUR', '156', 'Latest hour at which precipitation may end (168-12)', 'storm_multi/utils/validation.py'),
                ]),
                ('Sequence Type Probabilities', [
                    ('P(sequence|minimal)', '0.05', 'Probability of multi-storm sequence for minimal category', 'storm_multi/generators/intensity_sampler.py'),
                    ('P(sequence|baseline)', '0.15', 'Probability of multi-storm sequence for baseline category', 'storm_multi/generators/intensity_sampler.py'),
                    ('P(sequence|moderate)', '0.30', 'Probability of multi-storm sequence for moderate category', 'storm_multi/generators/intensity_sampler.py'),
                    ('P(sequence|severe)', '0.50', 'Probability of multi-storm sequence for severe category', 'storm_multi/generators/intensity_sampler.py'),
                    ('P(sequence|extreme)', '0.70', 'Probability of multi-storm sequence for extreme category', 'storm_multi/generators/intensity_sampler.py'),
                    ('P(sequence|catastrophic)', '0.85', 'Probability of multi-storm sequence for catastrophic category', 'storm_multi/generators/intensity_sampler.py'),
                ]),
                ('Storm Duration Parameters (min, mode, max hours)', [
                    ('minimal', '(2, 6, 12)', 'Triangular duration range for minimal category', 'storm_multi/generators/duration_sampler.py'),
                    ('baseline', '(6, 12, 24)', 'Triangular duration range for baseline category', 'storm_multi/generators/duration_sampler.py'),
                    ('moderate', '(12, 30, 60)', 'Triangular duration range for moderate category', 'storm_multi/generators/duration_sampler.py'),
                    ('severe', '(24, 48, 96)', 'Triangular duration range for severe category', 'storm_multi/generators/duration_sampler.py'),
                    ('extreme', '(36, 72, 144)', 'Triangular duration range for extreme category', 'storm_multi/generators/duration_sampler.py'),
                    ('catastrophic', '(48, 120, 240)', 'Triangular duration range for catastrophic category', 'storm_multi/generators/duration_sampler.py'),
                ]),
                ('Inter-Storm Gap Parameters (min, mode, max hours)', [
                    ('SHORT (persistent)', '(6, 18, 36)', 'Minimal drainage gap for persistent sequences', 'storm_multi/generators/gap_sampler.py'),
                    ('MEDIUM (doublet, cluster)', '(24, 48, 72)', 'Partial drainage gap for doublet/cluster sequences', 'storm_multi/generators/gap_sampler.py'),
                ]),
                ('Intensity Sampling', [
                    ('base_intensity_moderate', 'N(1.0, 0.20)', 'Normal base intensity for moderate category', 'port/src/storm_multi/generators/batch_generator.py'),
                    ('base_intensity_severe', 'N(1.8, 0.30)', 'Normal base intensity for severe category', 'port/src/storm_multi/generators/batch_generator.py'),
                    ('base_intensity_extreme', 'N(3.0, 0.50)', 'Normal base intensity for extreme category', 'port/src/storm_multi/generators/batch_generator.py'),
                    ('base_intensity_catastrophic', 'N(5.0, 0.80)', 'Normal base intensity for catastrophic category', 'port/src/storm_multi/generators/batch_generator.py'),
                    ('INTENSITY_VARIATION', '±0.20', 'Per-storm intensity variation around base (±20%)', 'storm_multi/generators/intensity_sampler.py'),
                    ('CORRELATION_PROB', '0.70', 'Probability subsequent storm ≥ first storm intensity', 'storm_multi/generators/intensity_sampler.py'),
                    ('peak_position_alpha', '2.0', 'Beta distribution shape α for peak position', 'storm_multi/generators/sequence_generator.py'),
                    ('peak_position_beta', '2.0', 'Beta distribution shape β for peak position', 'storm_multi/generators/sequence_generator.py'),
                ]),
                ('Batch Generation Defaults', [
                    ('default_count', '10000', 'Default number of sequences per batch', 'storm_multi/generators/batch_generator.py'),
                    ('weight_moderate', '0.40', 'Default intensity weight for moderate category', 'storm_multi/generators/batch_generator.py'),
                    ('weight_severe', '0.35', 'Default intensity weight for severe category', 'storm_multi/generators/batch_generator.py'),
                    ('weight_extreme', '0.20', 'Default intensity weight for extreme category', 'storm_multi/generators/batch_generator.py'),
                    ('weight_catastrophic', '0.05', 'Default intensity weight for catastrophic category', 'storm_multi/generators/batch_generator.py'),
                    ('catchment_base_precip_thames', '35.0 mm', 'Thames catchment base precipitation', 'storm_multi/generators/sequence_generator.py'),
                ]),
            ],
        },
    ]
