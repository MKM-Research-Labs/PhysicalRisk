# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Model Governance — Validation Questions (SR 11-7) and Overall Risk Rating.

Sub-modules:
- questions: Validation Questions tab (9 key questions, edit forms, save)
- risk_rating: Overall Risk Rating tab (composite score, MRC override)
"""

from ._js import get_js

__all__ = ["get_js"]
