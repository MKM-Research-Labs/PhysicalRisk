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

"""Shared baseline, fault geometry and per-cell metrics for the seismic
sensitivity harness.

The harness runs the *actual* end-to-end model (``simulate_asset_seismic``)
against the Section 7.1 baseline and varies one axis at a time, reporting the
resilience-credit currency the PRS pricer consumes (no-collapse rate, loss
frequency and the full-collapse seismic spread in bps).

Distance is controlled with a short (~2 km) fault segment: because the rupture
is clipped to the fault endpoints it always sits near the asset's perpendicular
foot, so the Joyner-Boore distance R_JB tracks the asset's offset cleanly.
"""

from dataclasses import replace

import numpy as np

from config.seismic import SeismicRunConfig, load_seismic_config
from models.seismic.damage import simulate_asset_seismic
from models.seismic.datastructures import AssetSeismicFeatures
from models.seismic.occurrence import parse_fault_trace

N_SIM = 20000
SEED = 20260608

# A short ~2 km E-W fault at latitude 21.0; assets are placed due south of its
# midpoint so the perpendicular distance == R_JB.
FAULT_LAT = 21.0
FAULT_LON = 106.01
FAULT = parse_fault_trace([[106.00, FAULT_LAT], [106.02, FAULT_LAT]])

# Model zone label -> CDM SeismicHazardClass that resolves to it.
HAZARD_CLASS = {
    "Very low": "None", "Low": "Low", "Moderate": "Medium",
    "High": "High", "Very high": "Extreme",
}
ZONES = ["Very low", "Low", "Moderate", "High", "Very high"]

# Section 7.4 Table 5 BRI positions (cumulative).
_B = ["GS01", "GS05", "GS07", "GS10", "GS11", "GS14"]
_A = _B + ["GS02", "GS08", "GS09", "GS15", "GS16"]
_AA = _A + ["GS03", "GS12", "GS13", "GS17", "GS18"]
BRI = {
    "NR": frozenset(), "B": frozenset(_B),
    "A": frozenset(_A), "AA": frozenset(_AA),
}

# Construction classes for the construction interaction (Appendix E1 keys).
CONSTRUCTION = {
    "RC pre-code": "RC_PreCode", "Masonry URM": "Masonry_URM",
    "RC modern": "RC_Modern", "Steel MRF": "Steel_MRF",
}

# Eurocode site-class V_S30 proxies (m/s) for the soft-soil interaction.
VS30 = {"Rock (A)": 800.0, "Stiff (B)": 450.0, "Soft (D)": 150.0}

_CFG = None


def cfg():
    """The hydrated seismic config at the harness draw count (cached)."""
    global _CFG
    if _CFG is None:
        _CFG = load_seismic_config(run=SeismicRunConfig(n_sim=N_SIM))
    return _CFG


def at_distance(r_jb_km):
    """Asset latitude placing it ~r_jb_km perpendicular south of the fault."""
    return FAULT_LAT - r_jb_km / 111.0


def baseline(r_jb_km=20.0):
    """Section 7.1 baseline: 4-storey Office, RC pre-code, Stiff soil (class B),
    Moderate zone, 20 km from the fault, all BRI measures absent."""
    return AssetSeismicFeatures(
        asset_id="C-SEIS-BASE",
        commercial_type="Office",
        construction_type="RC_PreCode",
        number_of_storeys=4,
        latitude=at_distance(r_jb_km),
        longitude=FAULT_LON,
        soil_vs30_mps=450.0,
        seismic_hazard_class="Medium",
        property_condition="Fair",
        measures=frozenset(),
    )


def metrics(features, seed=SEED):
    """Run the model once -> (median PGA g, no-collapse %, loss %, spread bps)."""
    result = simulate_asset_seismic(
        features, cfg(), FAULT, np.random.default_rng(seed))
    pgas = sorted(o.pga_g for o in result.outcomes)
    median_pga = pgas[len(pgas) // 2] if pgas else 0.0
    return (median_pga, 100.0 * result.no_collapse_rate,
            100.0 * result.loss_frequency, result.seismic_spread_bps)


# Re-exported for the table builders.
__all__ = [
    "N_SIM", "SEED", "FAULT", "HAZARD_CLASS", "ZONES", "BRI", "CONSTRUCTION",
    "VS30", "cfg", "at_distance", "baseline", "metrics", "replace",
]
