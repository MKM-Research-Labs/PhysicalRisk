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

"""Shared fixtures for pipeline integration tests."""

import pytest

from config import config

N_GAUGES = 5
N_PROPERTIES = 5
N_STORMS = 50
SIMULATION_HOURS = 12
HISTORY_YEARS = 5


def _run_pipeline(output_dir):
    """Execute all pipeline steps with small counts."""
    from port.src.gauge import GaugePortfolioGenerator
    from port.src.property import PropertyPortfolioGenerator
    from port.src.mortgage import MortgagePortfolioGenerator
    from port.src.gauge.gaugets import GaugeTimeSeriesGenerator
    from port.src.storm_multi.generators.batch_generator import generate_event_set
    from port.src.storm_multi.utils.serialization import save_sequences, save_summary
    from port.src.gauge.gaugehd import generate_all_gauge_histories
    from port.src.hazard import build_hazard_curves
    from port.src.property.propertyts import PropertyTimeSeriesGenerator
    from port.src.property.propertyhc import PropertyHazardCurveGenerator
    from port.src.counterparty import CounterpartyPortfolioGenerator

    GaugePortfolioGenerator(output_dir, verbose=False).generate(count=N_GAUGES)
    PropertyPortfolioGenerator(output_dir, verbose=False).generate(count=N_PROPERTIES)
    MortgagePortfolioGenerator(output_dir, verbose=False).generate()
    GaugeTimeSeriesGenerator(output_dir, verbose=False).generate(simulation_hours=SIMULATION_HOURS)
    # Generate storm sequences (replaces old generate_storms)
    sequences = generate_event_set(count=N_STORMS, catchment_id='thames', seed=42)
    save_sequences(sequences, output_dir / 'storm_sequences.json')
    save_summary(sequences, output_dir / 'sequences_summary.json')
    generate_all_gauge_histories(years=HISTORY_YEARS)
    build_hazard_curves(
        output_dir=output_dir, catchment_id='thames',
        distribution='gev', verbose=False,
    )
    PropertyTimeSeriesGenerator(output_dir, verbose=False).generate()
    PropertyHazardCurveGenerator(output_dir, verbose=False).generate()
    CounterpartyPortfolioGenerator(output_dir, verbose=False).generate()


@pytest.fixture(scope="module")
def pipeline_dir(tmp_path_factory):
    """Run a mini pipeline once per module; yield the directory.

    Module scope prevents config.input_dir mutations in generators.py
    from racing with the fixture setup for integration.py.
    """
    d = tmp_path_factory.mktemp("pipeline")
    original_input_dir = config.input_dir
    config.input_dir = d
    try:
        _run_pipeline(d)
        yield d
    finally:
        config.input_dir = original_input_dir
