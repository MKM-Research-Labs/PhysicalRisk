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

"""Spatial Interpolation Model sensitivity analysis."""

from docs.models.sensitivities import latex_table, write_tables


def generate():
    """Generate spatial interpolation sensitivity tables."""
    from models.floodrisk.spatial import idw_interpolate_from_gauges

    # Reference: 3 gauges at varying distances with known WSE values
    base_gauges = [
        (500.0, 12.5),    # 500m away, WSE 12.5m
        (2000.0, 11.8),   # 2km away, WSE 11.8m
        (5000.0, 10.2),   # 5km away, WSE 10.2m
    ]

    # Table 1: Sensitivity to IDW power parameter
    powers = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0]
    rows = []
    for p in powers:
        wse = idw_interpolate_from_gauges(base_gauges, power=p)
        rows.append([p, round(wse, 3)])

    t1 = latex_table(
        'Interpolated WSE sensitivity to IDW power parameter (3 gauges).',
        'sens_power',
        ['Power $p$', 'WSE (m)'],
        rows,
    )

    # Table 2: Sensitivity to nearest gauge distance
    distances = [100, 250, 500, 1000, 2000, 5000, 10000]
    rows = []
    for d in distances:
        gauges = [(float(d), 12.5), (2000.0, 11.8), (5000.0, 10.2)]
        wse = idw_interpolate_from_gauges(gauges, power=2.0)
        rows.append([d, round(wse, 3)])

    t2 = latex_table(
        'Interpolated WSE sensitivity to nearest gauge distance ($p=2$).',
        'sens_distance',
        ['Nearest gauge (m)', 'WSE (m)'],
        rows,
    )

    # Table 3: Sensitivity to number of gauges
    all_gauges = [
        (500.0, 12.5), (1200.0, 12.0), (2000.0, 11.8),
        (3500.0, 11.0), (5000.0, 10.2),
    ]
    rows = []
    for n in range(1, len(all_gauges) + 1):
        wse = idw_interpolate_from_gauges(all_gauges[:n], power=2.0)
        rows.append([n, round(wse, 3)])

    t3 = latex_table(
        'Interpolated WSE sensitivity to number of contributing gauges ($p=2$).',
        'sens_ngauges',
        ['Gauges used', 'WSE (m)'],
        rows,
    )

    write_tables('spatial_model', '\n\n'.join([t1, t2, t3]))
