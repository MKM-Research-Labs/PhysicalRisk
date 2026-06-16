# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Shared (catchment-agnostic) commercial asset random generators.

One implementation drives every catchment. Per-catchment data (archetype
tables, BRI regime, construction-year strategy) lives in the catchment
profile (``port.rand.profiles.<catchment>``); the generators read it via
``active_profile()``. The per-catchment ``port.rand.<catchment>.commercial``
trees are thin aliases of this package.
"""
