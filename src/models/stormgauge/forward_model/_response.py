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

"""Full gauge-response simulation (intensity + water-level timeseries)."""

from typing import List

from ..data_structures import GaugeConfig, GaugeResponse, Storm


class _ResponseMixin:
    """Simulate a storm's water-level response timeseries at gauges."""

    def compute_response(
        self,
        storm: Storm,
        gauge: GaugeConfig,
    ) -> GaugeResponse:
        """
        Compute full gauge response to a storm event.

        Simulates both intensity and water level timeseries,
        extracting summary statistics.
        """
        # Generate time points
        num_steps = int(storm.duration_hours / self.time_resolution_hours) + 1
        times = [i * self.time_resolution_hours for i in range(num_steps)]

        # Compute intensity timeseries at gauge
        intensity_ts = []
        for t in times:
            intensity = self.compute_intensity_at_gauge(
                t, gauge.longitude, gauge.latitude, storm
            )
            intensity_ts.append({"time_hours": t, "intensity": intensity})

        # Find peak intensity
        intensities = [p["intensity"] for p in intensity_ts]
        peak_intensity = max(intensities)
        peak_intensity_idx = intensities.index(peak_intensity)
        peak_intensity_time = times[peak_intensity_idx]

        # Convert intensity to water level with lag and decay
        level_ts = []
        current_contribution = 0.0

        for i, t in enumerate(times):
            lag_steps = int(self.response_lag_hours / self.time_resolution_hours)
            lagged_idx = max(0, i - lag_steps)
            lagged_intensity = intensities[lagged_idx]

            target_contribution = self.intensity_to_level(lagged_intensity, gauge)

            decay_rate = self.time_resolution_hours / self.response_decay_hours
            if target_contribution > current_contribution:
                current_contribution += (target_contribution - current_contribution) * min(1.0, decay_rate * 3)
            else:
                current_contribution += (target_contribution - current_contribution) * decay_rate

            level = gauge.base_level + current_contribution
            level_ts.append({"time_hours": t, "level": level})

        # Extract summary statistics
        levels = [p["level"] for p in level_ts]
        peak_level = max(levels)
        peak_idx = levels.index(peak_level)
        peak_time = times[peak_idx]
        peak_exceedance = peak_level - gauge.flood_alert

        dt = self.time_resolution_hours
        duration_alert = sum(dt for l in levels if l >= gauge.flood_alert)
        duration_warning = sum(dt for l in levels if l >= gauge.flood_warning)
        duration_severe = sum(dt for l in levels if l >= gauge.severe_warning)

        accumulation = sum(
            max(0, l - gauge.flood_alert) * dt
            for l in levels
        )

        return GaugeResponse(
            gauge_id=gauge.gauge_id,
            storm_id=storm.storm_id,
            flooded=peak_level >= gauge.flood_alert,
            peak_level=peak_level,
            peak_exceedance=peak_exceedance,
            peak_time_hours=peak_time,
            peak_intensity=peak_intensity,
            peak_intensity_time_hours=peak_intensity_time,
            duration_above_alert=duration_alert,
            duration_above_warning=duration_warning,
            duration_above_severe=duration_severe,
            accumulation=accumulation,
            intensity_timeseries=intensity_ts,
            level_timeseries=level_ts,
        )

    def compute_all_responses(
        self,
        storm: Storm,
        gauges: List[GaugeConfig],
    ) -> List[GaugeResponse]:
        """Compute responses for all gauges."""
        return [self.compute_response(storm, g) for g in gauges]
