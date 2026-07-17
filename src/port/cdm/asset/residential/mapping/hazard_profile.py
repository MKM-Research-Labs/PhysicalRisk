# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Flatten ProtectionMeasures.HazardProfile (normalised hazard classes)."""


def flatten_hazard_profile(prop: dict) -> dict:
    """Return flat snake_case keys for the four hazard classes and design intensities."""
    hp = prop.get("ProtectionMeasures", {}).get("HazardProfile", {})

    return {
        "flood_hazard_class":   hp.get("FloodHazardClass"),
        "wind_hazard_class":    hp.get("WindHazardClass"),
        "seismic_hazard_class": hp.get("SeismicHazardClass"),
        "fire_hazard_class":    hp.get("FireHazardClass"),
        "design_wind_speed_kmh":    hp.get("DesignWindSpeedKmh"),
        "design_flood_return_yr":   hp.get("DesignFloodReturnYr"),
        "design_seismic_pga":       hp.get("DesignSeismicPGA"),
    }
