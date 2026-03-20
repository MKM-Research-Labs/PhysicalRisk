# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Flood damage assessment claim report package.

Public API:
    from reports.property.claim import ClaimReportGenerator
"""

from .generator import ClaimReportGenerator

__all__ = ['ClaimReportGenerator']
