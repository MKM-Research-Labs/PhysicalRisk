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

"""Portfolio/trading parameter registry — split submodule. See config.port."""

from typing import Dict, List


# ===========================================================================
# Data Lineage  (lineage/manifest.py, routes/governance/lineage.py)
# ===========================================================================

# Chunk size for streaming SHA-256 file hashing (bytes)
LINEAGE_CHUNK_SIZE: int = 65536

# Pipeline staleness threshold — steps older than this are flagged (hours)
LINEAGE_STALE_HOURS: int = 72


# ===========================================================================
# Trading — Severity Ordering  (routes/trading/port_stress.py)
# ===========================================================================

# Sort key for gauge stress results (lower = more severe)
SEVERITY_ORDER: Dict[str, int] = {
    'severe': 0,
    'warning': 1,
    'alert': 2,
    'clean': 3,
}


# ===========================================================================
# Entity ID Naming Standards
# ===========================================================================
# Prefixes used when constructing STORM-xxx, GAUGE-xxx identifiers.
# All ID generators must read from these constants — never inline the prefix.

STORM_ID_PREFIX: str = "STORM"      # e.g. STORM-3f1a9c2b
GAUGE_ID_PREFIX: str = "GAUGE"      # e.g. GAUGE-0180833d
SEQUENCE_ID_PREFIX: str = "STORM"   # e.g. STORM-d0ef339e (unified prefix)


# ===========================================================================
# Stress Storms Catalogue  (port/src/gauge/stress_storms.py)
# ===========================================================================

# Minimum number of alert-breaching storms required in stress_storms.json
STRESS_STORMS_MIN_COUNT: int = 50

# Hydrograph defaults used when storm metadata is not stored in gaugets
STRESS_STORM_DEFAULT_DURATION_HOURS: int = 168
STRESS_STORM_DEFAULT_PEAK_POSITION: float = 0.5


# ===========================================================================
# Spatial Correlation Model  (storm_multi/models/spatial_correlation.py)
# ===========================================================================
# Thames-calibrated exponential correlation kernel (spec: Storm Generator
# Spatial Correlation Spec, Section 5 / Table 2).
# Previously persisted as data/input/thames/spatial_correlation.json.

# Spatial correlation switched on by default
SPATIAL_CORR_ENABLED: bool = True

# Kernel type — only "exponential" is implemented
SPATIAL_CORR_MODEL_TYPE: str = "exponential"

# Correlation range at intensity_factor = 1 (~half the Thames corridor, km)
SPATIAL_CORR_BASE_RANGE_KM: float = 40.0

# Nugget: micro-scale variability added to the diagonal (5%)
SPATIAL_CORR_NUGGET: float = 0.05

# Range scaling: range_km increases by rho_intensity per unit intensity_factor
# above 1, so extreme storms are more spatially coherent
SPATIAL_CORR_RHO_INTENSITY: float = 0.40

# Log-space standard deviation of the spatial precipitation field (40% CoV)
SPATIAL_CORR_SIGMA_LOGNORMAL: float = 0.40

# Default Thames gauge count — used as documentary metadata when writing
# spatial correlation config; the live model uses the actual gauge list
SPATIAL_CORR_NUM_GAUGES: int = 52
