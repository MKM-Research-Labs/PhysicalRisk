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

"""Storm Intensity sensitivity analysis."""

from docs.models.sensitivities import latex_table, write_tables


def generate():
    """Generate storm intensity sensitivity tables."""
    from models.intensity.distribution import IntensityDistribution

    # Table 1: Tail index sensitivity
    tail_indices = [1.5, 2.0, 2.5, 3.0]
    return_periods = [10, 25, 50, 100]
    headers = [r'$\alpha$ (tail index)'] + [f'{rp}-yr intensity' for rp in return_periods]
    rows = []
    for alpha in tail_indices:
        dist = IntensityDistribution(
            base_mean=40, base_std=12, tail_threshold=65,
            tail_index=alpha, min_intensity=10, max_intensity=100)
        vals = [round(dist.return_period_intensity(rp, storms_per_year=20), 1) for rp in return_periods]
        rows.append([alpha] + vals)

    t1 = latex_table(
        'Storm intensity at return periods by Pareto tail index (base mean=40, std=12, threshold=65).',
        'sens_tail_index', headers, rows,
    )

    # Table 2: Base mean sensitivity
    base_means = [30, 35, 40, 45, 50]
    headers = ['Base mean'] + [f'{rp}-yr intensity' for rp in return_periods]
    rows = []
    for bm in base_means:
        dist = IntensityDistribution(
            base_mean=bm, base_std=12, tail_threshold=65,
            tail_index=2.0, min_intensity=10, max_intensity=100)
        vals = [round(dist.return_period_intensity(rp, storms_per_year=20), 1) for rp in return_periods]
        rows.append([bm] + vals)

    t2 = latex_table(
        'Storm intensity at return periods by base mean ($\\alpha=2.0$, std=12, threshold=65).',
        'sens_base_mean', headers, rows,
    )

    # Table 3: Exceedance probabilities
    intensities = [40, 50, 60, 70, 80, 90]
    headers = ['Intensity'] + [f'$\\alpha={a}$' for a in [1.5, 2.0, 2.5, 3.0]]
    rows = []
    for intensity in intensities:
        exc_vals = []
        for alpha in [1.5, 2.0, 2.5, 3.0]:
            dist = IntensityDistribution(
                base_mean=40, base_std=12, tail_threshold=65,
                tail_index=alpha, min_intensity=10, max_intensity=100)
            exc_vals.append(round(dist.exceedance_probability(intensity), 6))
        rows.append([intensity] + exc_vals)

    t3 = latex_table(
        'Exceedance probability by storm intensity and tail index.',
        'sens_exceedance', headers, rows,
    )

    write_tables('storm_intensity', '\n\n'.join([t1, t2, t3]))
