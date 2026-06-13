# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""Combined JS fragment for the validation and risk-rating tabs."""

from . import questions, risk_rating


def get_js():
    """Return combined JS fragment for validation and risk rating tabs."""
    return (questions.get_js() +
            risk_rating.get_js())
