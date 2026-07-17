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

"""Shared predicates for the wind-coupled hazard stages."""

import database

from ...context import StageContext


def _damage_available(ctx: StageContext) -> bool:
    """True when typhoon damage exists for this catchment (the typhoon_event
    seam artifact, i.e. the EVT-* damage records)."""
    return any(database.iter_typhoon_event_ids(database.active_catchment()))


def _peril_requested(ctx: StageContext) -> bool:
    a = ctx.args
    return any(getattr(a, f, False) for f in (
        "propertytsw", "propertytsfaw", "propertytsfow",
        "propertytsbow", "propertytsbaw",
        "propertywin", "propertyfaw", "propertyfow",
        "propertybow", "propertybaw",
    ))


def _commercial_peril_requested(ctx: StageContext) -> bool:
    a = ctx.args
    return any(getattr(a, f, False) for f in (
        "commercialtsw", "commercialtsfaw", "commercialtsfow",
        "commercialtsbow", "commercialtsbaw",
        "commercialwin", "commercialfaw", "commercialfow",
        "commercialbow", "commercialbaw",
    ))
