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

#
# This software is provided under license by MKM Research Labs.
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Gauge Time Series Generator.

Generates synthetic flood gauge time series data for simulating
flood events across a catchment's gauge network.

Output: per-gauge JSON files in gaugets/ directory, each containing
the flood simulation readings for that gauge.

Usage:
    from config import config
    from gaugets import GaugeTimeSeriesGenerator, generate_gaugets

    # Option 1: Use convenience function (uses config.CATCHMENT)
    result = generate_gaugets(simulation_hours=72)

    # Option 2: Use generator class with config defaults
    generator = GaugeTimeSeriesGenerator()
    result = generator.generate(simulation_hours=72)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np

from config import config

logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


class GaugeTimeSeriesGenerator:
    """
    Gauge Time Series Generator.

    Generates synthetic time series data simulating flood events
    for all gauges in the gauge portfolio. Outputs one JSON file
    per gauge in the gaugets/ directory.
    """

    DEFAULT_PARAMS = {
        "simulation_hours": 168,
        "time_step_hours": 1,
        "peak_hour_min": 36,
        "peak_hour_max": 84,
        "peak_hour_stagger": 2,
        "base_amplitude": 0.5,
        "peak_amplitude": 2.0,
        "recession_rate": 0.02
    }

    def __init__(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        random_module: Optional[Any] = None,
        catchment_params: Optional[Any] = None,
        verbose: bool = True
    ):
        self.output_dir = Path(output_dir) if output_dir else config.get_input_dir()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        if not verbose:
            logging.getLogger(__name__).setLevel(logging.WARNING)

        self.random = random_module or config.load_random_module('gauge.gaugets_random')
        self.params = catchment_params or config.load_params_module()

        self.sim_params = self.DEFAULT_PARAMS.copy()

    def log(self, message: str, level: str = "INFO"):
        """Log processing information."""
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(message)

    def configure(self, **kwargs):
        """Configure simulation parameters."""
        for key, value in kwargs.items():
            if key in self.sim_params:
                self.sim_params[key] = value
                self.log(f"Set {key} = {value}", "DEBUG")

    def generate(self, simulation_hours: int = 168) -> Dict:
        """
        Generate gauge time series data as per-gauge files.

        Args:
            simulation_hours: Hours to simulate (default: 168)

        Returns:
            Dictionary with generated data and metadata
        """
        self.sim_params['simulation_hours'] = simulation_hours

        self.log("Gauge Time Series Generator", "INFO")
        self.log(f"Catchment: {config.CATCHMENT}", "INFO")
        self.log(f"Simulation hours: {self.sim_params['simulation_hours']}", "INFO")

        # Load gauge portfolio
        gauge_portfolio_path = config.get_input_path("gauge.json")
        self.log(f"Loading gauges from: {gauge_portfolio_path}", "INFO")

        try:
            with open(gauge_portfolio_path, 'r') as f:
                gauge_data = json.load(f)
            gauges = gauge_data.get('flood_gauges', [])
            self.log(f"Loaded {len(gauges)} gauges", "SUCCESS")
        except FileNotFoundError:
            self.log(f"Gauge portfolio not found: {gauge_portfolio_path}", "ERROR")
            raise FileNotFoundError(
                f"Gauge portfolio not found at {gauge_portfolio_path}. "
                "Generate gauges first using GaugePortfolioGenerator."
            )

        # Generate time series using random module
        self.log("Generating time series data...", "INFO")
        time_series_data = self.random.generate_flood_simulation(gauges, self.sim_params)
        self.log(f"Generated {len(time_series_data)} timesteps", "SUCCESS")

        # Reorganize into per-gauge data and write per-gauge files
        gaugets_dir = self.output_dir / "gaugets"
        gaugets_dir.mkdir(parents=True, exist_ok=True)

        # Remove stale gauge files from previous runs (GAUGE-* and SYNTH-*)
        for stale in gaugets_dir.glob('GAUGE-*.json'):
            stale.unlink()
        for stale in gaugets_dir.glob('SYNTH-*.json'):
            stale.unlink()

        # Build per-gauge readings from the interleaved timestep data
        gauge_readings = {}  # gauge_id -> list of readings
        for timestep in time_series_data:
            for reading in timestep.get('readings', []):
                gauge_id = reading.get('gaugeId')
                if gauge_id:
                    if gauge_id not in gauge_readings:
                        gauge_readings[gauge_id] = []
                    gauge_readings[gauge_id].append(reading)

        # Write per-gauge files
        for gauge_id, readings in gauge_readings.items():
            gauge_file = gaugets_dir / f"{gauge_id}.json"
            gauge_data = {
                "gauge_id": gauge_id,
                "metadata": {
                    "catchment": config.CATCHMENT,
                    "generated_at": datetime.now().isoformat(),
                    "generator_version": "4.0",
                },
                "flood_simulation": {
                    "simulation_hours": self.sim_params['simulation_hours'],
                    "num_timesteps": len(readings),
                    "readings": readings,
                },
            }

            with open(gauge_file, 'w') as f:
                json.dump(gauge_data, f, indent=2, cls=DateTimeEncoder)

        self.log(f"Saved {len(gauge_readings)} per-gauge files to: {gaugets_dir}", "SUCCESS")

        return {
            "data": {
                "time_series": time_series_data,
                "num_gauges": len(gauges),
                "num_timesteps": len(time_series_data)
            },
            "file_path": gaugets_dir,
            "simulation_parameters": self.sim_params
        }


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def generate_gaugets(simulation_hours: int = 168) -> Dict:
    """
    Convenience function to generate gauge time series for current catchment.

    Uses config.CATCHMENT to determine which random module and params to use.

    Args:
        simulation_hours: Hours to simulate (default: 168)

    Returns:
        Generation result dictionary
    """
    generator = GaugeTimeSeriesGenerator()
    return generator.generate(simulation_hours)


if __name__ == "__main__":
    logger.info(f"Generating gauge time series for catchment: {config.CATCHMENT}")
    result = generate_gaugets(168)
    logger.info(f"Generated {result['data']['num_timesteps']} timesteps for {result['data']['num_gauges']} gauges.")
    logger.info(f"Output saved to: {result['file_path']}")
