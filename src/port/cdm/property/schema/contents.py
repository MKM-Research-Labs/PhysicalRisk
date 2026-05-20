# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""PropertyHeader.Contents — replacement value and vulnerability of building contents."""

CONTENTS_SCHEMA = {
    "ContentsValue": {
        "type": "decimal",
        "description": "Replacement value of contents in local currency"
    },
    "ContentsMobility": {
        "type": "menu",
        "options": ["Fixed", "Moveable", "Mixed"],
        "description": "Whether contents are fixed in place or removable"
    },
    "ContentsStoredAboveFlood": {
        "type": "boolean",
        "description": "Primary contents stored above design flood level"
    },
}
