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
Synthetic timeseries generation model for flood gauges.

Generates realistic daily water level timeseries that respect:
- Gauge-specific flood thresholds (FloodAlert, FloodWarning, SevereFloodWarning)
- Historical high levels and dates from the gauge portfolio
- Seasonal patterns (higher levels in winter)
- Appropriate flood frequency based on historical records

Model components:
    - Base level: fraction of FloodAlert threshold
    - Seasonal variation: cosine with winter peak (day 15)
    - Daily noise: Gaussian perturbation
    - Flood injection: Poisson-distributed severe and minor events
    - Historical high placement: exact date matching
"""

import math
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


def generate_synthetic_timeseries(
    gauge_data: Dict[str, Any],
    years: int = 50,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Generate synthetic daily water level timeseries for a gauge.

    Uses gauge-specific thresholds and historical data to create
    realistic patterns including seasonal variation, random daily
    fluctuation, occasional flood events, and historical high levels.

    Args:
        gauge_data: FloodGauge CDM data from gauge portfolio
        years: Number of years of history to generate
        seed: Random seed for reproducibility

    Returns:
        List of daily observations with date and level_meters
    """
    if seed is not None:
        random.seed(seed)

    # Extract gauge parameters
    flood_gauge = gauge_data.get("FloodGauge", gauge_data)
    flood_stages = flood_gauge.get("FloodStages", {})
    sensor_stats = flood_gauge.get("SensorStats", {})
    gauge_info = (flood_gauge.get("SensorDetails", {})
                  .get("GaugeInformation", {}))

    flood_alert = flood_stages.get("FloodAlert", 3.0)
    flood_warning = flood_stages.get("FloodWarning", 4.0)
    severe_warning = flood_stages.get("SevereFloodWarning", 5.0)
    historical_high = sensor_stats.get("HistoricalHighLevel", severe_warning * 1.1)
    historical_high_date = sensor_stats.get("HistoricalHighDate")
    freq_exceed_level3 = sensor_stats.get("FrequencyExceedLevel3", 0)

    # Tidal influence — controls daily variability
    tidal_influence = gauge_info.get("TidalInfluence", "Non-tidal")
    is_tidal = tidal_influence == "Tidal"
    is_partial_tidal = tidal_influence == "Partially tidal"

    # Calculate base parameters
    base_level = flood_alert * random.uniform(0.3, 0.5)

    # Tidal gauges: larger daily swing (tidal range), lower noise
    # Non-tidal upstream gauges: very stable day-to-day, change driven by rainfall
    if is_tidal:
        daily_std = base_level * 0.20       # tidal range creates wider spread
        seasonal_amplitude = base_level * 0.20  # seasonal less dominant vs tide
        tidal_amplitude = base_level * 0.15     # semi-diurnal tidal swing
        autocorrelation = 0.6               # moderate — tide resets twice daily
    elif is_partial_tidal:
        daily_std = base_level * 0.12
        seasonal_amplitude = base_level * 0.22
        tidal_amplitude = base_level * 0.06     # dampened tidal signal
        autocorrelation = 0.75
    else:
        daily_std = base_level * 0.08       # upstream: very stable
        seasonal_amplitude = base_level * 0.30  # seasonal dominates
        tidal_amplitude = 0.0               # no tidal influence
        autocorrelation = 0.85              # high — river level changes slowly

    # Generate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)

    # Parse historical high date if available
    historical_high_dt = None
    if historical_high_date:
        try:
            historical_high_dt = datetime.strptime(historical_high_date, "%Y-%m-%d")
            if historical_high_dt < start_date or historical_high_dt > end_date:
                historical_high_dt = None
        except ValueError:
            pass

    # Flood event probabilities
    severe_floods_expected = max(freq_exceed_level3, 1)
    severe_flood_prob_per_day = severe_floods_expected / (years * 365)
    minor_flood_prob_per_day = severe_flood_prob_per_day * 5

    daily_observations = []
    current_date = start_date
    historical_high_placed = False
    prev_deviation = 0.0  # for autocorrelation (AR(1) process)

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")

        if historical_high_dt and current_date.date() == historical_high_dt.date():
            level = historical_high
            historical_high_placed = True
            prev_deviation = level - base_level  # reset AR state
        else:
            # Seasonal component (higher in winter: Nov-Feb)
            day_of_year = current_date.timetuple().tm_yday
            seasonal = seasonal_amplitude * math.cos(2 * math.pi * (day_of_year - 15) / 365)

            # Tidal component (spring-neap ~14.8 day cycle)
            tidal = 0.0
            if tidal_amplitude > 0:
                # Spring-neap modulation: amplitude varies over ~14.8 day lunar cycle
                lunar_phase = (day_of_year % 14.8) / 14.8
                spring_neap = 0.6 + 0.4 * math.cos(2 * math.pi * lunar_phase)
                tidal = tidal_amplitude * spring_neap * random.uniform(-1, 1)

            # AR(1) noise — today's deviation depends on yesterday's
            innovation = random.gauss(0, daily_std * math.sqrt(1 - autocorrelation**2))
            prev_deviation = autocorrelation * prev_deviation + innovation

            level = base_level + seasonal + tidal + prev_deviation

            # Check for flood events (Poisson injection)
            if random.random() < severe_flood_prob_per_day:
                level = random.uniform(severe_warning, historical_high * 0.95)
                prev_deviation = level - base_level  # flood resets AR state
            elif random.random() < minor_flood_prob_per_day:
                level = random.uniform(flood_alert, flood_warning)
                prev_deviation = level - base_level

            level = max(0.1, level)

        daily_observations.append({
            "date": date_str,
            "level_meters": round(level, 3)
        })

        current_date += timedelta(days=1)

    # Inject historical high if not yet placed
    if historical_high_dt and not historical_high_placed:
        for obs in daily_observations:
            if obs["date"] == historical_high_date:
                obs["level_meters"] = historical_high
                break

    return daily_observations
