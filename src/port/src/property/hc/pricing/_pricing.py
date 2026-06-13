# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Composition of the property pricing mixins into ``PricingMixin``."""

from ._process import _ProcessMixin
from ._wind import _WindMixin


class PricingMixin(_ProcessMixin, _WindMixin):
    """Mixin providing property processing, PRS pricing, and basis methods."""
