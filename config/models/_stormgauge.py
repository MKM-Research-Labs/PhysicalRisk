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
"""Storm-Gauge Forward Model parameters (MKM-SG-001 v2.0, ``models/stormgauge``).

Table 3 of the model document: the grid, the lag, and the two time constants of
Eq. 16 -- the gauge rises towards its target with ``stormgauge_rise_hours`` and falls
with ``stormgauge_decay_hours``. v1.0-1.3 tied the rise to the fall (3 dt / tau_decay,
a 4-hour rise), so no storm reached the levels the calibration named; the Wolfram
benchmark v0.1 (04-Nov-2026) found it, and v2.0 sets the rise apart at 1 hour.

The run continues ``stormgauge_recession_decays`` fall constants past the storm's
end, with no forcing, so durations and accumulation count the whole recession
(e^-5: the level is within 0.7% of where it started falling).
"""

stormgauge_time_resolution_hours = 0.5
stormgauge_lag_hours = 2.0
stormgauge_rise_hours = 1.0
stormgauge_decay_hours = 12.0
stormgauge_recession_decays = 5

# Eq. 13: the power-law exponent; s3.5: the historical high, where a gauge has none,
# as a multiple of its severe level; Eqs. 1-2: the Earth's radius (km).
stormgauge_gamma = 0.8
stormgauge_high_of_severe = 1.1
stormgauge_earth_radius_km = 6371.0
