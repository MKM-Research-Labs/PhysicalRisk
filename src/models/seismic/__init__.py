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

"""Building Seismic-Resilience Credit Model (MKM-SEIS-001).

Four governance-separated component models that price the seismic resilience of
a commercial asset into the same resilience-credit currency as the storm, wind
and fire engines:

- Model A — Occurrence (Poisson) + fault-geometry spatial draw (occurrence.py)
- Model B — Ground Motion Intensity / GMPE (groundmotion.py)
- Model C — Seismic Response Effectiveness (responseeffectiveness.py)
- Model D — Damage State, Loss & Resilience Credit + orchestrator (damage.py)

The model reads only the CDM-derived :class:`AssetSeismicFeatures` bundle
(datastructures.py), never the raw CDM record, so the feature contract is
explicit and stable against CDM schema churn. Stage 0 delivers the parameter
contract (config/seismic.py), the feature bundle and the CDM adapter; Models
A-D follow in later stages.
"""
