# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Thames (UK) rand-generation profile — catchment-specific data only.

The shared property/commercial generators read these via
``port.rand.profiles.active_profile()``. Generation LOGIC is shared; only the
values that genuinely differ by catchment live here.
"""

# Seismic — UK intraplate: low PGA, None/Low-weighted hazard class.
SEISMIC_PGA_RANGE = (0.02, 0.08)
SEISMIC_HAZARD_CLASS_WEIGHTS = [0.70, 0.28, 0.02, 0.00, 0.00]

# BRI regime: Thames has no certified BRI letter-rating regime.
PUBLISH_BRI_LETTER_RATINGS = False
BRI_SCORES_ENABLED = False
