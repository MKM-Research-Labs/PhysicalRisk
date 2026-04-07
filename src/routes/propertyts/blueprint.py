# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Property flood timeseries Flask blueprint and route registration.

Creates the propertyts_bp Blueprint and imports all sub-modules to register
their routes.
"""

from flask import Blueprint

from ._helpers import _get_propertyts_dir  # noqa: F401

propertyts_bp = Blueprint('propertyts', __name__)
