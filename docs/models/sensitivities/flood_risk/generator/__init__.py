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

"""Flood Risk (depth-damage) sensitivity analysis."""

from docs.models.sensitivities import latex_table, write_tables


def generate():
    """Generate flood risk sensitivity tables."""
    from models.floodrisk.depth_damage import scalar_depth_damage
    from models.floodrisk.velocity import (
        compute_manning_velocity, compute_attenuation
    )

    # Table 1: Depth-damage curve
    depths = [0.0, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0]
    rows = [[d, round(scalar_depth_damage(d), 4)] for d in depths]

    t1 = latex_table(
        'Depth-damage function: damage ratio by flood depth.',
        'sens_depth_damage',
        ['Depth (m)', 'Damage ratio'], rows,
    )

    # Table 2: Manning's velocity sensitivity to roughness
    roughness_vals = [0.02, 0.03, 0.04, 0.05, 0.06, 0.08]
    depth_vals = [0.5, 1.0, 2.0]
    slope = 0.005
    headers = ["Manning's $n$"] + [f'$v$ at $d={d}$m' for d in depth_vals]
    rows = []
    for n in roughness_vals:
        velocities = [round(compute_manning_velocity(d, slope, n), 3) for d in depth_vals]
        rows.append([n] + velocities)

    t2 = latex_table(
        "Manning's velocity (m/s) by roughness coefficient ($S=0.005$).",
        'sens_manning_roughness', headers, rows,
    )

    # Table 3: Attenuation by distance and decay length
    distances = [0, 500, 1000, 2000, 5000, 10000]
    decay_lengths = [1000, 2000, 3000, 5000]
    headers = ['Distance (m)'] + [f'$L={l}$m' for l in decay_lengths]
    rows = []
    for d in distances:
        atts = [round(compute_attenuation(d, length=l), 4) for l in decay_lengths]
        rows.append([d] + atts)

    t3 = latex_table(
        'Attenuation factor by distance and characteristic length.',
        'sens_attenuation', headers, rows,
    )

    write_tables('flood_risk', '\n\n'.join([t1, t2, t3]))
