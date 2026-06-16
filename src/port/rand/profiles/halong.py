# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Halong (coastal Vietnam) rand-generation profile — catchment-specific data.

The shared property/commercial generators read these via
``port.rand.profiles.active_profile()``. Generation LOGIC is shared; only the
values that genuinely differ by catchment live here.
"""

# Seismic — Halong sits on the Red River Fault Zone, rated High by the
# MKM-SEIS-001 hazard table: higher PGA, Medium/High-weighted hazard class.
SEISMIC_PGA_RANGE = (0.12, 0.50)
SEISMIC_HAZARD_CLASS_WEIGHTS = [0.05, 0.15, 0.35, 0.30, 0.15]

# BRI regime: Halong publishes certified BRI letter ratings + numeric scores.
PUBLISH_BRI_LETTER_RATINGS = True
BRI_SCORES_ENABLED = True
