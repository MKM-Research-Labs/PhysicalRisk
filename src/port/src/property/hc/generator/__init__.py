# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

"""
Property-Level Hazard Curve Generator with PRS Pricing and Basis Calculation.

For each property in the propertyts output:
1. Counts severe flood events from the Monte Carlo simulation
2. Computes spread as event_count / num_scenarios (bp)
3. Calculates basis vs synthetic gauge spread
4. Attaches spread decomposition (gauge → SHD → SHE → property)

Usage:
    from port.src.property.hc import PropertyHazardCurveGenerator
    generator = PropertyHazardCurveGenerator(output_dir)
    result = generator.generate()
"""

from ._generator import PropertyHazardCurveGenerator

__all__ = ["PropertyHazardCurveGenerator"]
