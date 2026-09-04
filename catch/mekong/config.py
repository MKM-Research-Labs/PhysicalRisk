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

"""Mekong catchment definition — Phnom Penh, Cambodia (lower Mekong).

Centred on the Chaktomuk confluence (Tonlé Sap + Mekong → Bassac) at Phnom
Penh, with gauges along the three rivers through and around the city and a
Phnom-Penh commercial-district footprint. Values are denominated in USD.

The class structure and method signatures are kept identical to the other
catchments (BaseCatchment subclass) so the rest of the pipeline (port
generators, hazard, visualisation) works unchanged.

Usage:
    from catch.mekong import MekongCatchment
    catchment = MekongCatchment()
    locations = catchment.generate_synchronized_locations(10)
"""

from typing import Dict, List, Tuple
import math
import random

from ..base import BaseCatchment


# =============================================================================
# MODULE-LEVEL CONSTANTS
# =============================================================================

# Gauge points along the lower Mekong system through Phnom Penh, ordered
# upstream (Tonlé Sap, NW) → confluence → downstream (Bassac / Mekong, SE).
# (lat, lon, elevation_meters). Phnom Penh sits ~10-12 m above sea level on a
# flat floodplain; bank levels fall gently downstream.
GAUGE_POINTS = [
    (11.8090, 104.8090, 11.8),   # 0 Prek Kdam (Tonlé Sap River)
    (11.6400, 104.9120, 11.3),   # 1 Chroy Changvar (north peninsula)
    (11.5850, 104.9290, 11.0),   # 2 Chaktomuk Confluence (Phnom Penh Port)
    (11.5620, 104.9310, 10.8),   # 3 Sisowath Quay (riverfront)
    (11.5400, 104.9340, 10.6),   # 4 Monivong Bridge (Bassac)
    (11.4980, 104.9400, 10.3),   # 5 Takhmau (Bassac, southern suburb)
    (11.4500, 105.0000, 10.0),   # 6 Koki (lower Mekong, SE)
]

# One name per GAUGE_POINTS entry, ordered upstream → downstream.
GAUGE_NAMES = [
    "Prek Kdam (Tonlé Sap)",   # 0
    "Chroy Changvar",          # 1
    "Chaktomuk Confluence",    # 2
    "Sisowath Quay",           # 3
    "Monivong Bridge",         # 4
    "Takhmau",                 # 5
    "Koki (Lower Mekong)",     # 6
]

# Phnom Penh khans (districts) spanning the riverside and inner city.
AREAS = [
    "Daun Penh",        # central riverfront / CBD
    "Chamkarmon",       # embassies, BKK1 — prime commercial
    "Prampi Makara",    # central, dense commercial
    "Tuol Kouk",        # inner north-west
    "Chroy Changvar",   # peninsula across the confluence
    "Mean Chey",        # southern, industrial
    "Russey Keo",       # northern riverside
    "Sen Sok",          # north-west growth corridor
]

# Street names by Phnom Penh district (small starter set per AREAS entry).
STREETS = {
    "Daun Penh": [
        "Sisowath Quay", "Norodom Boulevard", "Street 51 (Pasteur)",
        "Monivong Boulevard", "Street 110",
    ],
    "Chamkarmon": [
        "Street 240", "Mao Tse Toung Boulevard", "Sothearos Boulevard",
        "Street 63", "Norodom Boulevard",
    ],
    "Prampi Makara": [
        "Kampuchea Krom Boulevard", "Street 182", "Charles de Gaulle Boulevard",
        "Monireth Boulevard", "Street 217",
    ],
    "Tuol Kouk": [
        "Street 289", "Russian Federation Boulevard", "Kim Il Sung Boulevard",
        "Street 315", "Street 337",
    ],
    "Chroy Changvar": [
        "National Road 6A", "Riverside Road", "Prek Leap Road",
        "Build Bright Street", "Street CC",
    ],
    "Mean Chey": [
        "Hun Sen Boulevard", "National Road 2", "Veng Sreng Road",
        "Street 271", "Samdach Monireth Boulevard",
    ],
    "Russey Keo": [
        "National Road 5", "Toul Sangke Road", "Street 598",
        "Street 1019", "Khan Russey Keo Road",
    ],
    "Sen Sok": [
        "Russian Federation Boulevard", "Hanoi Road", "Street 2004",
        "Sen Sok Street", "Street 1986",
    ],
}

# Property value factor by district. Riverside CBD (Daun Penh) and the
# embassy / BKK1 belt (Chamkarmon) carry a premium; northern and southern
# fringe khans sit below the city average.
AREA_VALUE_FACTORS = {
    "Daun Penh": 1.8,
    "Chamkarmon": 1.7,
    "Prampi Makara": 1.4,
    "Tuol Kouk": 1.2,
    "Chroy Changvar": 1.1,
    "Mean Chey": 0.9,
    "Russey Keo": 0.85,
    "Sen Sok": 1.0,
}

# Cambodian flood decision bodies.
FLOOD_DECISION_BODIES = [
    "National Committee for Disaster Management (NCDM)",
    "Ministry of Water Resources and Meteorology (MOWRAM)",
    "Phnom Penh Capital Administration (Capital Hall)",
    "Mekong River Commission (MRC)",
]

# Gauge owners along the lower Mekong / Tonlé Sap.
GAUGE_OWNERS = [
    "Ministry of Water Resources and Meteorology (MOWRAM)",
    "Department of Hydrology and River Works",
    "Mekong River Commission (MRC)",
    "Royal University of Phnom Penh — Faculty of Hydrology",
]

# Data curators.
DATA_CURATORS = [
    "Ministry of Water Resources and Meteorology (MOWRAM)",
    "Mekong River Commission (MRC)",
    "ADB / World Bank flood datasets",
    "Phnom Penh Capital Hall Open Data",
]

# Cambodian commercial banks active in Phnom Penh mortgage / CRE lending.
MORTGAGE_LENDERS = [
    "ABA Bank", "ACLEDA Bank", "Canadia Bank", "Cambodian Public Bank (Campu)",
    "Vattanac Bank", "Sathapana Bank", "Wing Bank", "Prince Bank",
    "Phillip Bank", "Chip Mong Commercial Bank",
]

# Geographic bounds for greater Phnom Penh (min_lon, min_lat, max_lon, max_lat).
# Comfortably contains every gauge plus the ~1 km property-placement radius
# (Prek Kdam in the NW and Koki in the SE set the extremes).
BOUNDS = (104.78, 11.40, 105.06, 11.84)

# Center point: Chaktomuk confluence, central Phnom Penh.
CENTER_LAT = 11.5564
CENTER_LON = 104.9282

# Base property value in USD — a mid-range central Phnom Penh commercial unit.
BASE_PROPERTY_VALUE = 500_000

# ISO 4217 currency code for valuations, loans, PRS trade notionals.
CURRENCY = "USD"

# Elevation model parameters — the lower Mekong floodplain is very flat.
MAXSLOPEPERCENT = 0.5
MAXRANDOMELEVATION = 5.0


# =============================================================================
# MEKONG CATCHMENT CLASS
# =============================================================================

class MekongCatchment(BaseCatchment):
    """Lower Mekong catchment — Phnom Penh, Cambodia.

    Centred on the Chaktomuk confluence with gauges along the Tonlé Sap,
    Mekong and Bassac through the city, eight Phnom Penh khans, and Cambodian
    banks / agencies for stamping commercial loan and gauge records. Property
    values are denominated in USD.
    """

    # Expose module-level constants as class attributes
    NAME = "mekong"
    REGION = "Asia"
    DISPLAYNAME = "Mekong (Phnom Penh)"
    COUNTRY = "Cambodia"

    GAUGE_POINTS = GAUGE_POINTS
    GAUGEPOINTS = GAUGE_POINTS  # Alias for compatibility
    GAUGE_NAMES = GAUGE_NAMES
    AREAS = AREAS
    STREETS = STREETS
    AREA_VALUE_FACTORS = AREA_VALUE_FACTORS
    AREAVALUEFACTORS = AREA_VALUE_FACTORS  # Alias for compatibility

    FLOOD_DECISION_BODIES = FLOOD_DECISION_BODIES
    GAUGE_OWNERS = GAUGE_OWNERS
    DATA_CURATORS = DATA_CURATORS
    MORTGAGE_LENDERS = MORTGAGE_LENDERS

    BOUNDS = BOUNDS
    CENTER_LAT = CENTER_LAT
    CENTER_LON = CENTER_LON
    BASE_PROPERTY_VALUE = BASE_PROPERTY_VALUE

    MAXSLOPEPERCENT = MAXSLOPEPERCENT
    MAXRANDOMELEVATION = MAXRANDOMELEVATION

    def get_random_gauge_point(self) -> Tuple[float, float, float]:
        """Get a random gauge point along the river with elevation."""
        return self.GAUGE_POINTS[random.randint(0, len(self.GAUGE_POINTS) - 1)]

    def calculate_location_near_thames(self, distancemeters: float = None) -> Dict:
        """Generate a random location near the river system.

        (Method name retained for cross-catchment pipeline compatibility.)
        """
        gaugepointidx = random.randint(0, len(self.GAUGE_POINTS) - 1)
        gaugepoint = self.GAUGE_POINTS[gaugepointidx]

        if distancemeters is None:
            distancemeters = random.uniform(100, 1000)

        latdegpermeter = 1 / 111000
        londegpermeter = 1 / (69400 * math.cos(math.radians(gaugepoint[0])))

        anglerad = math.radians(random.uniform(0, 360))
        latoffset = distancemeters * latdegpermeter * math.cos(anglerad)
        lonoffset = distancemeters * londegpermeter * math.sin(anglerad)

        newlat = gaugepoint[0] + latoffset
        newlon = gaugepoint[1] + lonoffset

        areaname = self.AREAS[gaugepointidx % len(self.AREAS)]

        return {
            "lat": newlat,
            "lon": newlon,
            "elevation": gaugepoint[2],
            "name": areaname,
            "gaugepointidx": gaugepointidx,
            "distancetothames": distancemeters,
            "valuefactor": self.AREA_VALUE_FACTORS.get(areaname, 1.0),
        }

    def generate_synchronized_locations(self, count: int) -> List[Dict]:
        """Generate a list of locations near the river system with elevations."""
        locations = []

        for i in range(min(count, len(self.GAUGE_POINTS))):
            gaugepoint = self.GAUGE_POINTS[i]
            distancemeters = random.uniform(100, 1000)

            latdegpermeter = 1 / 111000
            londegpermeter = 1 / (69400 * math.cos(math.radians(gaugepoint[0])))

            anglerad = math.radians(random.uniform(0, 360))
            latoffset = distancemeters * latdegpermeter * math.cos(anglerad)
            lonoffset = distancemeters * londegpermeter * math.sin(anglerad)

            newlat = gaugepoint[0] + latoffset
            newlon = gaugepoint[1] + lonoffset

            areaname = self.AREAS[i % len(self.AREAS)]

            locations.append({
                "lat": newlat,
                "lon": newlon,
                "elevation": gaugepoint[2],
                "name": areaname,
                "gaugepointidx": i,
                "distancetothames": distancemeters,
                "valuefactor": self.AREA_VALUE_FACTORS.get(areaname, 1.0),
            })

        if count > len(self.GAUGE_POINTS):
            for _ in range(len(self.GAUGE_POINTS), count):
                locations.append(self.calculate_location_near_thames())

        return locations

    def get_thames_elevation_at_point(self, pointidx: int) -> float:
        """Get the elevation at a specific gauge point.

        (Method name retained for cross-catchment pipeline compatibility.)
        """
        if 0 <= pointidx < len(self.GAUGE_POINTS):
            return self.GAUGE_POINTS[pointidx][2]
        raise IndexError(
            f"Gauge point index {pointidx} out of range "
            f"(0-{len(self.GAUGE_POINTS) - 1})")

    def get_streets_for_area(self, areaname: str) -> List[str]:
        """Get street names for a given district (empty if not found)."""
        return self.STREETS.get(areaname, [])
