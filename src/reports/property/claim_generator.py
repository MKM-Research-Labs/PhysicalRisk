# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

"""Backward-compatibility shim.

The claim report has been modularised into the ``reports.property.claim``
package.  Import directly from there:

    from reports.property.claim import ClaimReportGenerator
"""

from reports.property.claim import ClaimReportGenerator  # noqa: F401

__all__ = ['ClaimReportGenerator']
