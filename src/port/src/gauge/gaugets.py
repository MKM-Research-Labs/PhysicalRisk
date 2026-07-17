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

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import database
from config import config

logger = logging.getLogger(__name__)


from port.utils.encoders import DateTimeEncoder  # noqa: F401


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
        catchment: Optional[str] = None,
        random_module: Optional[Any] = None,
        catchment_params: Optional[Any] = None,
        verbose: bool = True
    ):
        # Run-scoped catchment identity; storage location lives in ``database``.
        self.catchment = catchment or database.active_catchment()
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

        # Load gauge portfolio through the database seam.
        gauge_portfolio = database.get_gauge_portfolio(self.catchment)
        if gauge_portfolio is None:
            self.log(f"Gauge portfolio not found for catchment: {self.catchment}", "ERROR")
            raise FileNotFoundError(
                f"Gauge portfolio not found for catchment {self.catchment}. "
                "Generate gauges first using GaugePortfolioGenerator."
            )
        gauges = gauge_portfolio.get('flood_gauges', [])
        self.log(f"Loaded {len(gauges)} gauges", "SUCCESS")

        # Generate time series using random module
        self.log("Generating time series data...", "INFO")
        time_series_data = self.random.generate_flood_simulation(gauges, self.sim_params)
        self.log(f"Generated {len(time_series_data)} timesteps", "SUCCESS")

        # Remove stale per-gauge timeseries from previous runs, then write fresh.
        for stale_id in list(database.iter_gauge_timeseries_ids(self.catchment)):
            database.delete_gauge_timeseries(self.catchment, stale_id)

        # Build per-gauge readings from the interleaved timestep data
        gauge_readings = {}  # gauge_id -> list of readings
        for timestep in time_series_data:
            for reading in timestep.get('readings', []):
                gauge_id = reading.get('gaugeId')
                if gauge_id:
                    if gauge_id not in gauge_readings:
                        gauge_readings[gauge_id] = []
                    gauge_readings[gauge_id].append(reading)

        # Write per-gauge timeseries through the database seam.
        for gauge_id, readings in gauge_readings.items():
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
            database.save_gauge_timeseries(self.catchment, gauge_id, gauge_data)

        self.log(f"Saved {len(gauge_readings)} per-gauge timeseries for catchment: {self.catchment}", "SUCCESS")

        return {
            "data": {
                "time_series": time_series_data,
                "num_gauges": len(gauges),
                "num_timesteps": len(time_series_data)
            },
            "catchment": self.catchment,
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
    logger.info(f"Saved to catchment: {result['catchment']}")
