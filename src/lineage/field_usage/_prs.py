# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see ../auth.py for full license text)

"""Direct PRS pricing inputs (RED) that do not pass through a damage function.

Valuation drives the notional / loss amount; the reference gauges select the
hazard-curve basket that prices the swap. Keys are CDM dotted paths from the
record root.
"""

from .tiers import RED

_PRS = "PRS pricing"


def _valuation_entry():
    return {
        "tier": RED,
        "summary": "Asset value sets the PRS notional / loss-at-risk that the spread is "
                   "applied to.",
        "consumers": [_PRS],
        "chain": [
            {"node": "PropertyValue (CDM)", "kind": "field"},
            {"node": "notional / loss-at-risk", "kind": "function",
             "ref": "src/port/src/property/hc/pricing"},
            {"node": "PRS premium / protection leg", "kind": "output"},
        ],
    }


PRS_FIELDS = {
    "PropertyHeader.Valuation.PropertyValue": _valuation_entry(),
    "CommercialAsset.Valuation.PropertyValue": _valuation_entry(),
    "PropertyHeader.Contents.ContentsValue": {
        "tier": RED,
        "summary": "Contents replacement value adds to the loss-at-risk priced by the PRS.",
        "consumers": [_PRS],
        "chain": [
            {"node": "ContentsValue (CDM)", "kind": "field"},
            {"node": "loss-at-risk", "kind": "function"},
            {"node": "PRS protection leg", "kind": "output"},
        ],
    },
    "PropertyHeader.ReferenceGauges": {
        "tier": RED,
        "summary": "Reference gauges select the hazard-curve basket that prices the swap — "
                   "the flood hazard transmitted to this asset.",
        "consumers": ["MKM-GH-001 hazard curves", _PRS],
        "chain": [
            {"node": "ReferenceGauges (CDM)", "kind": "field"},
            {"node": "IDW gauge basket", "kind": "function",
             "ref": "src/port/src/property/hc"},
            {"node": "property hazard curve", "kind": "output",
             "ref": "data/input/<catchment>/propertyhc.json"},
            {"node": "PRS flood spread (bps)", "kind": "output"},
        ],
    },
}
