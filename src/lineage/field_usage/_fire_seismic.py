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

"""Fire and seismic model field chains (RED — feed the PRS spread).

Both models run over the commercial portfolio, so the construction/risk paths
use the ``CommercialAsset`` header; the BRI scores live under the shared
``ProtectionMeasures`` block. Source of truth: ``src/models/fire/`` and
``src/models/seismic/``.
"""

from .tiers import RED

_FIRE = "MKM-FIRE-001 fire"
_SEIS = "MKM-SEIS-001 seismic"
_PRS = "PRS spread"

FIRE_SEISMIC_FIELDS = {
    "ProtectionMeasures.RiskAssessment.GoverningBodyRatings.BRIFireScore": {
        "tier": RED,
        "summary": "Fire resilience score; modulates ignition / containment in the fire "
                   "model whose loss frequency feeds the PRS spread.",
        "consumers": [_FIRE, _PRS],
        "chain": [
            {"node": "BRIFireScore (CDM)", "kind": "field"},
            {"node": "fire occurrence / containment", "kind": "function",
             "ref": "src/models/fire/"},
            {"node": "fire loss frequency", "kind": "output",
             "ref": "data/input/<catchment>/fire/fire.json"},
            {"node": "PRS spread (bps)", "kind": "output"},
        ],
    },
    "ProtectionMeasures.RiskAssessment.GoverningBodyRatings.BRISeismicScore": {
        "tier": RED,
        "summary": "Seismic resilience score; shifts the fragility curve, feeding the "
                   "seismic loss frequency and the PRS spread.",
        "consumers": [_SEIS, _PRS],
        "chain": [
            {"node": "BRISeismicScore (CDM)", "kind": "field"},
            {"node": "seismic fragility / damage", "kind": "function",
             "ref": "src/models/seismic/damage.py"},
            {"node": "seismic loss frequency", "kind": "output",
             "ref": "data/input/<catchment>/seismic/seismic.json"},
            {"node": "PRS spread (bps)", "kind": "output"},
        ],
    },
    "CommercialAsset.Construction.ConstructionType": {
        "tier": RED,
        "summary": "Construction type drives the fire combustibility leg and the seismic "
                   "fragility class, feeding both peril spreads.",
        "consumers": [_FIRE, _SEIS, _PRS],
        "chain": [
            {"node": "ConstructionType (CDM)", "kind": "field"},
            {"node": "fire combustibility / seismic class", "kind": "function",
             "ref": "src/models/fire/, src/models/seismic/"},
            {"node": "fire & seismic loss frequency", "kind": "output"},
            {"node": "PRS spread (bps)", "kind": "output"},
        ],
    },
    "CommercialAsset.RiskAssessment.SoilVs30Mps": {
        "tier": RED,
        "summary": "Shear-wave velocity resolves the seismic site class, scaling ground "
                   "motion in the fragility curve and the PRS seismic spread.",
        "consumers": [_SEIS, _PRS],
        "chain": [
            {"node": "SoilVs30Mps (CDM)", "kind": "field"},
            {"node": "site class / ground motion", "kind": "function",
             "ref": "src/models/seismic/groundmotion.py"},
            {"node": "seismic loss frequency", "kind": "output"},
            {"node": "PRS spread (bps)", "kind": "output"},
        ],
    },
}
