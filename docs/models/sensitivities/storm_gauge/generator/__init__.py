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

"""Storm-Gauge model sensitivity analysis."""

from docs.models.sensitivities import latex_table, write_tables


def generate():
    """Generate storm-gauge sensitivity tables."""
    from models.stormgauge.forward_model import StormGaugeModel
    from models.stormgauge.data_structures import DecayKernel, GaugeConfig

    # Table 1: Spatial decay by kernel type
    model = StormGaugeModel(intensity_to_level_scale=0.1)
    distances = [0, 25, 50, 75, 100, 150, 200]
    footprint = 100.0
    headers = ['Distance (km)', 'Gaussian', 'Exponential', 'Linear']
    rows = []
    for d in distances:
        g = round(model.compute_decay(d, footprint, DecayKernel.GAUSSIAN, 1.0), 4)
        e = round(model.compute_decay(d, footprint, DecayKernel.EXPONENTIAL, 1.0), 4)
        lin = round(model.compute_decay(d, footprint, DecayKernel.LINEAR, 1.0), 4)
        rows.append([d, g, e, lin])

    t1 = latex_table(
        'Spatial decay factor by kernel type (footprint=100\\,km, decay\\_param=1.0).',
        'sens_decay_kernel', headers, rows,
    )

    # Table 2: Intensity-to-level conversion sensitivity
    scales = [0.05, 0.08, 0.10, 0.12, 0.15, 0.20]
    intensities = [20, 40, 60, 80, 100]
    headers = ['Scale'] + [f'$I={i}$' for i in intensities]
    rows = []
    for s in scales:
        m = StormGaugeModel(intensity_to_level_scale=s)
        gauge = GaugeConfig(
            gauge_id='TEST', gauge_name='Test', latitude=51.5, longitude=-0.1,
            base_level=1.5, flood_alert=3.0, flood_warning=4.0,
            severe_warning=5.0, historical_high=6.0, sensitivity=1.0,
        )
        levels = [round(m.intensity_to_level(i, gauge), 3) for i in intensities]
        rows.append([s] + levels)

    t2 = latex_table(
        'Water level contribution (m) by intensity and scale factor (gauge sensitivity=1.0).',
        'sens_intensity_level', headers, rows,
    )

    write_tables('storm_gauge', '\n\n'.join([t1, t2]))
