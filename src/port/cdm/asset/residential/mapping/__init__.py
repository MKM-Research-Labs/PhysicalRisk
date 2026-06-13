# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
Residential asset CDM mapping package.

Composes create_mapping() from per-category flatten functions. Each module
mirrors the corresponding schema section.
"""

from ._mapping import create_mapping

__all__ = ["create_mapping"]
