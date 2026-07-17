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

"""Timeseries Statistics sensitivity analysis."""

import datetime
import math

import numpy as np

from docs.models.sensitivities import latex_table, write_tables


def generate():
    """Generate timeseries statistics sensitivity tables."""
    from models.statistics.timeseries import calculate_timeseries_statistics

    # Generate synthetic data with known properties
    np.random.seed(42)
    n_years = 20
    n_days = int(n_years * 365.25)
    start = datetime.date(2000, 1, 1)
    observations = []
    for i in range(n_days):
        d = start + datetime.timedelta(days=i)
        day_of_year = d.timetuple().tm_yday
        seasonal = 2.0 + 0.5 * math.sin(2 * math.pi * (day_of_year - 30) / 365.25)
        noise = np.random.normal(0, 0.3)
        level = max(0.5, seasonal + noise)
        observations.append({'date': d.isoformat(), 'level_meters': round(level, 3)})

    flood_stages = {'FloodAlert': 3.0, 'FloodWarning': 3.5, 'SevereFloodWarning': 4.0}

    # Table 1: Sensitivity to flood alert threshold
    alert_thresholds = [2.5, 2.75, 3.0, 3.25, 3.5]
    rows = []
    for threshold in alert_thresholds:
        stages = {'FloodAlert': threshold, 'FloodWarning': 3.5, 'SevereFloodWarning': 4.0}
        stats = calculate_timeseries_statistics(observations, 'level_meters', stages)
        exc = stats.get('flood_exceedances', {}).get('flood_alert', {})
        rows.append([threshold, exc.get('count', 0), round(exc.get('frequency_per_year', 0), 1)])

    t1 = latex_table(
        'Flood Alert exceedance sensitivity to threshold level (20-year synthetic record).',
        'sens_threshold',
        ['Alert Threshold (m)', 'Total Days', 'Days/Year'], rows,
    )

    # Table 2: Statistics summary
    stats = calculate_timeseries_statistics(observations, 'level_meters', flood_stages)
    summary_rows = [
        ['Mean level', f'{stats["mean_level_meters"]:.3f}'],
        ['Median level', f'{stats["median_level_meters"]:.3f}'],
        ['Std dev', f'{stats["std_dev"]:.3f}'],
        ['Min level', f'{stats["min_level_meters"]:.3f}'],
        ['Max level', f'{stats["max_level_meters"]:.3f}'],
        ['P5', f'{stats["percentiles"]["p5"]:.3f}'],
        ['P95', f'{stats["percentiles"]["p95"]:.3f}'],
        ['P99', f'{stats["percentiles"]["p99"]:.3f}'],
        ['Annual maxima mean', f'{stats["annual_maxima"]["mean"]:.3f}'],
        ['Annual maxima std', f'{stats["annual_maxima"]["std_dev"]:.3f}'],
    ]

    t2 = latex_table(
        'Summary statistics from 20-year synthetic water level record.',
        'sens_summary',
        ['Statistic', 'Value (m)'], summary_rows,
        col_fmt='lr',
    )

    write_tables('timeseries_statistics', '\n\n'.join([t1, t2]))
