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
Flood risk model package.

Splits the core flood risk engine into:
  - spatial: KDTree, correlation matrix, distance calculations
  - depth_damage: flood depths and vulnerability curves
  - velocity: Manning's equation, retention, hydrograph construction
  - risk_analytics: Monte Carlo, concentration, clustering
  - risk_visualization: Folium maps, matplotlib plots

Changelog:
  v2.0  Initial IDW + exponential retention model
  v2.1  Replace IDW with nearest-gauge-only; near-field retention bypass
        (Book 210 alignment: flow-aligned propagation, not isotropic averaging)
"""

MODEL_VERSION = "2.1"

# NOTE: FloodRiskModel is intentionally NOT imported here.
# flood_risk_model.py depends on geopandas which is an optional heavy GIS
# dependency.  Eagerly importing it at package level prevents depth_damage,
# spatial, and risk_analytics modules from being used without geopandas.
# Import directly: `from models.floodrisk.flood_risk_model import FloodRiskModel`

__all__ = []
