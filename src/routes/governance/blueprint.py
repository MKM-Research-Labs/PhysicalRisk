# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Model Risk Governance Flask blueprint and route registration.

Creates the governance_bp Blueprint and imports all sub-modules to register
their routes.
"""

from flask import Blueprint

governance_bp = Blueprint("governance", __name__)
