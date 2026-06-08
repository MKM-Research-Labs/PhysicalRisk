# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use is prohibited
# unless separately authorized in writing by MKM Research Labs.

"""Enumerations for the seismic model configuration."""

from enum import Enum


class DamageState(Enum):
    """The four HAZUS/GEM-style damage states of the fragility chain.

    The integer value is the threshold index: DS0 is the no-collapse floor,
    DS3 (complete / collapse) is the point-of-no-return analogue whose
    frequency the PRS pricer charges as the seismic spread.
    """
    DS0 = 0  # None / Slight
    DS1 = 1  # Moderate
    DS2 = 2  # Extensive
    DS3 = 3  # Complete / collapse


class SoilClass(Enum):
    """Eurocode 8 site classes derived from V_S30 (Appendix C2)."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
