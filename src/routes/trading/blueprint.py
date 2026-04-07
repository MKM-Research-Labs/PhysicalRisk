# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Trading desk Flask blueprint and route registration.

Creates the trading_bp Blueprint and imports all sub-modules to register
their routes. Sub-modules must be imported after the blueprint is defined
to avoid circular imports.
"""

from flask import Blueprint

from ._helpers import no_cache

trading_bp = Blueprint("trading", __name__)
trading_bp.after_request(no_cache)
