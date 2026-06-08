# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use is prohibited
# unless separately authorized in writing by MKM Research Labs.

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
