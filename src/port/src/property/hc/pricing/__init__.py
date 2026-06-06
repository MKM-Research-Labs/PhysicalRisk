# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.
"""Property pricing and basis calculation mixin for PropertyHazardCurveGenerator.

v3.0: Replaced GEV/CDS pricing with simple severe event count.
Spread (bp) = N(severe floods) / N(total scenarios) × 10,000.
Term structure is flat (storms are independent).

Stage 6 (peril outcomes): the pricer emits a ``prs_perils`` block with all
four peril outcomes at the property/BRI node (coupling_spec.md §11.6):

* ``flood_only``    — severe flood triggers (the flood spine, unchanged)
* ``wind_only``     — binary ``is_prs_wind`` damage-onset triggers
* ``flood_or_wind`` — union over the 1:1-paired event set (one denominator)
* ``flood_and_wind``— intersection (inclusion-exclusion: F + W − union)

The wind leg is the binary ``is_prs_wind`` damage-onset trigger — NOT the
continuous wind damage amount. The flood-only ``prs_spread_bps`` /
``term_structure.severe`` (flood spine) is kept unchanged: it still drives the
gauge basis and the flood-vs-gauge spread decomposition. Wind has no gauge
intermediary — it is a pure intersect/union at the property node. Catchments
without a typhoon stage emit no ``prs_perils`` block and are byte-identical to
before (flood-only fallback).
"""

from ._process import _ProcessMixin
from ._wind import _WindMixin

__all__ = ["PricingMixin"]


class PricingMixin(_ProcessMixin, _WindMixin):
    """Mixin providing property processing, PRS pricing, and basis methods."""
