# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Active-catchment map-centre helper for the storm interactivity maps."""


def catchment_map_center():
    """Return ``(lat, lon)`` centre of the active catchment for map init.

    Thin wrapper over :func:`config.visual.get_map_center` — the single
    source of truth — so the storm maps open over the catchment in play.
    """
    from config.visual import get_map_center
    return get_map_center()
