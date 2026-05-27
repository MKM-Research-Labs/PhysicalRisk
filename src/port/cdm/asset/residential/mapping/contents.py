# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Flatten PropertyHeader.Contents."""


def flatten_contents(prop: dict) -> dict:
    """Return flat snake_case keys for contents risk."""
    contents = prop.get("PropertyHeader", {}).get("Contents", {})

    return {
        "contents_value":             contents.get("ContentsValue"),
        "contents_mobility":          contents.get("ContentsMobility"),
        "contents_stored_above_flood": contents.get("ContentsStoredAboveFlood"),
    }
