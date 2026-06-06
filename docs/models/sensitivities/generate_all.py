#!/usr/bin/env python3

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
Generate sensitivity analysis tables for all (or specific) model documentation.

Calls each model with varying inputs and writes LaTeX table fragments
to <model_dir>/sensitivity_tables.tex for inclusion in the main doc.

Usage:
    python -m docs.models.sensitivities.generate_all
    python -m docs.models.sensitivities.generate_all --model prs gev
"""

import argparse
import sys
import os

# Add project root and src/ to path
_project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, _project_root)
sys.path.insert(0, os.path.join(_project_root, 'src'))

# Registry of all model sensitivity generators
GENERATORS = {
    'prs': ('PRS Pricing', 'docs.models.sensitivities.prs_pricing.generator'),
    'gev': ('GEV Hazard', 'docs.models.sensitivities.gev_hazard.generator'),
    'storm': ('Storm Intensity', 'docs.models.sensitivities.storm_intensity.generator'),
    'flood': ('Flood Risk', 'docs.models.sensitivities.flood_risk.generator'),
    'gauge': ('Storm-Gauge', 'docs.models.sensitivities.storm_gauge.generator'),
    'mortgage': ('Mortgage Pricer', 'docs.models.sensitivities.mortgage_pricer.generator'),
    'property': ('Property Valuation', 'docs.models.sensitivities.property_valuation.generator'),
    'risk': ('Risk Assessment', 'docs.models.sensitivities.risk_assessment.generator'),
    'ts': ('Timeseries Statistics', 'docs.models.sensitivities.timeseries_statistics.generator'),
    'classifier': ('Flood Classifier', 'docs.models.sensitivities.flood_classifier.generator'),
    'spatial': ('Spatial Interpolation', 'docs.models.sensitivities.spatial_model.generator'),
    'insurance': ('Insurance Premium', 'docs.models.sensitivities.insurance_premium.generator'),
    'delta': ('Delta Engine', 'docs.models.sensitivities.delta_engine.generator'),
    'stormmulti': ('Storm Sequence', 'docs.models.sensitivities.storm_multi.generator'),
    'gaugehd': ('GaugeHD Synthetic', 'docs.models.sensitivities.gaugehd_synthetic.generator'),
    'bri': ('Building Resilience Index', 'docs.models.sensitivities.bri_resilience.generator'),
    'fire': ('Fire-Resilience Credit', 'docs.models.sensitivities.fire_resilience.generator'),
}


def main():
    parser = argparse.ArgumentParser(
        description='Generate sensitivity analysis tables from actual model calls')
    parser.add_argument('--model', nargs='+',
                        help=f'Run specific models only. '
                             f'Available: {", ".join(sorted(GENERATORS.keys()))}')
    args = parser.parse_args()

    targets = args.model if args.model else list(GENERATORS.keys())

    print('Generating sensitivity tables from actual model calls...\n')

    for key in targets:
        if key not in GENERATORS:
            print(f'  Unknown model: {key}')
            print(f'  Available: {", ".join(sorted(GENERATORS.keys()))}')
            continue

        name, module_path = GENERATORS[key]
        print(f'[{name}]')
        try:
            import importlib
            mod = importlib.import_module(module_path)
            mod.generate()
        except Exception as e:
            print(f'  ERROR: {e}')
            import traceback
            traceback.print_exc()
        print()

    print('Done. Sensitivity tables written to each model directory.')
    print('Include in LaTeX with: \\input{sensitivity_tables}')


if __name__ == '__main__':
    main()
