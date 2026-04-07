# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Gauge API Flask blueprint and route registration.

Creates the gauges_bp Blueprint and imports all sub-modules to register
their routes.
"""

from flask import Blueprint

gauges_bp = Blueprint('gauges', __name__)
