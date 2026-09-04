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

"""
Halong catchment definition for Halong Bay, Vietnam.

This module is a thames-derived template — the gauge points, area names,
streets, value factors, lender list, and bounds below are still UK Thames
values and MUST be replaced with Halong-specific data before generating
a Halong portfolio. The class structure and method signatures are kept
identical to HalongCatchment so the rest of the pipeline (port generators,
hazard, visualisation) works unchanged.

Halong is configured as a commercial-only catchment with limited gauge
coverage and recalibrated storms relative to Thames.

Usage:
    from catch.halong import HalongCatchment
    catchment = HalongCatchment()
    locations = catchment.generate_synchronized_locations(10)
"""

from typing import Dict, List, Tuple
import math
import random

from ..base import BaseCatchment


# =============================================================================
# MODULE-LEVEL CONSTANTS (for backward compatibility with port.params.thames)
# =============================================================================

# Thames gauge points with elevation data (lat, lon, elevation_meters)
# Ordered west to east (upstream to downstream): Reading → Purfleet (52 total)
# Indices 0-11: non-tidal upstream reach (Reading to Teddington Lock)
# Indices 12-51: tidal Thames (Richmond Lock to Purfleet)
# Red River gauges through Hanoi (lat, lon, elevation_meters).
# Ordered upstream (NW) → downstream (SE), snapped near the polyline
# in river_polyline.json. Elevations reflect typical Red River bank
# levels around Hanoi (~5–10 m above sea level).
GAUGE_POINTS = [
    (21.0770, 105.8437, 9.00), (21.0439, 105.8633, 7.50),
    (21.0004, 105.8908, 6.00),
]

# Hanoi districts along the Red River (right bank + east bank).
AREAS = [
    "Tây Hồ",        # NW, by West Lake
    "Ba Đình",       # central government district
    "Hoàn Kiếm",     # old quarter
    "Long Biên",     # east bank, across the Red River
    "Hai Bà Trưng",  # south of Hoàn Kiếm
    "Hoàng Mai",     # south
    "Đống Đa",       # southwest of Hoàn Kiếm
]

# One name per GAUGE_POINTS entry, ordered upstream → downstream.
GAUGE_NAMES = [
    "Nhật Tân Bridge",    # 0
    "Long Biên Bridge",   # 1
    "Vĩnh Tuy Bridge",    # 2
]

# Street names by Hanoi district (small starter set per AREAS entry).
STREETS = {
    "Tây Hồ": [
        "Lạc Long Quân", "Âu Cơ", "Yên Phụ", "Quảng An", "Tô Ngọc Vân"
    ],
    "Ba Đình": [
        "Hoàng Diệu", "Điện Biên Phủ", "Phan Đình Phùng", "Kim Mã", "Liễu Giai"
    ],
    "Hoàn Kiếm": [
        "Tràng Tiền", "Hàng Bài", "Đinh Tiên Hoàng", "Phố Huế", "Hàng Bông"
    ],
    "Long Biên": [
        "Nguyễn Văn Cừ", "Ngô Gia Tự", "Ngọc Lâm", "Cổ Linh", "Nguyễn Sơn"
    ],
    "Hai Bà Trưng": [
        "Bà Triệu", "Lò Đúc", "Trần Khát Chân", "Minh Khai", "Đại Cồ Việt"
    ],
    "Hoàng Mai": [
        "Giải Phóng", "Trương Định", "Tân Mai", "Tam Trinh", "Lĩnh Nam"
    ],
    "Đống Đa": [
        "Tôn Đức Thắng", "Khâm Thiên", "Tây Sơn", "Nguyễn Lương Bằng", "Phạm Ngọc Thạch"
    ],
}

# Property value factor by Hanoi district. Central/embassy districts
# (Hoàn Kiếm, Ba Đình, Tây Hồ) carry a premium; eastern Long Biên and
# southern Hoàng Mai sit below the city average.
AREA_VALUE_FACTORS = {
    "Tây Hồ": 1.6,
    "Ba Đình": 1.5,
    "Hoàn Kiếm": 1.8,
    "Long Biên": 0.9,
    "Hai Bà Trưng": 1.2,
    "Hoàng Mai": 0.9,
    "Đống Đa": 1.3,
}

# Vietnamese flood decision bodies
FLOOD_DECISION_BODIES = [
    "Vietnam Disaster Management Authority (VDMA)",
    "Ministry of Agriculture and Rural Development (MARD)",
    "Hanoi People's Committee — Department of Construction",
    "Central Steering Committee for Natural Disaster Prevention and Control",
]

# Gauge owners around Hanoi / Red River
GAUGE_OWNERS = [
    "Vietnam Meteorological and Hydrological Administration (VMHA)",
    "Northern Region Hydrometeorological Center",
    "Red River Basin Authority",
    "Hanoi University of Natural Resources and Environment",
]

# Data curators
DATA_CURATORS = [
    "Vietnam Meteorological and Hydrological Administration (VMHA)",
    "Mekong River Commission (regional reference)",
    "ADB / World Bank flood datasets",
    "Hanoi People's Committee Open Data",
]

# Vietnam mortgage lenders (largest commercial banks active in Hanoi)
MORTGAGE_LENDERS = [
    "Vietcombank", "BIDV", "VietinBank", "Agribank", "Techcombank",
    "MB Bank", "VPBank", "ACB", "Sacombank", "HDBank",
]

# Geographic bounds for Hanoi central area (min_lon, min_lat, max_lon, max_lat).
BOUNDS = (105.78, 20.96, 105.96, 21.10)

# Center point: Hoàn Kiếm Lake, central Hanoi.
CENTER_LAT = 21.0285
CENTER_LON = 105.8542

# Base property value in USD. Roughly equivalent to a mid-range
# central-Hanoi commercial unit; recalibrate after first run.
BASE_PROPERTY_VALUE = 500_000

# ISO 4217 currency code for valuations, loans, PRS trade notionals.
CURRENCY = "USD"

# Elevation model parameters (Red River basin is flatter than the
# Thames — narrow band of riverside elevation).
MAXSLOPEPERCENT = 1.0
MAXRANDOMELEVATION = 6.0


# =============================================================================
# THAMES CATCHMENT CLASS
# =============================================================================

class HalongCatchment(BaseCatchment):
    """Halong / Hanoi Red River catchment (Vietnam) — commercial-only.

    First-pass calibration: 3 gauges along the Red River through central
    Hanoi (Nhật Tân → Long Biên → Vĩnh Tuy), 7 right- and east-bank
    districts, and Vietnamese banks / agencies for stamping commercial
    loan and gauge records. Property values are denominated in USD.

    Storm parameters in ``port/rand/halong`` are still thames-shaped
    and will need recalibration for the South China Sea typhoon regime
    before storms are generated.
    """
    
    # Expose module-level constants as class attributes
    NAME = "halong"
    REGION = "Asia"
    DISPLAYNAME = "Halong"
    COUNTRY = "Vietnam"
    
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
        """Get a random point along the Thames with elevation."""
        point = self.GAUGE_POINTS[random.randint(0, len(self.GAUGE_POINTS) - 1)]
        return point
    
    def calculate_location_near_thames(self, distancemeters: float = None) -> Dict:
        """
        Generate a random location near the Thames.
        
        Args:
            distancemeters: Distance from the Thames in meters (100-1000)
                           If None, a random distance is chosen
                           
        Returns:
            Dictionary with location information
        """
        gaugepointidx = random.randint(0, len(self.GAUGE_POINTS) - 1)
        gaugepoint = self.GAUGE_POINTS[gaugepointidx]
        
        if distancemeters is None:
            distancemeters = random.uniform(100, 1000)
        
        # Convert distance to degrees
        latdegpermeter = 1 / 111000
        londegpermeter = 1 / (69400 * math.cos(math.radians(gaugepoint[0])))
        
        # Generate random angle
        anglerad = math.radians(random.uniform(0, 360))
        
        # Calculate offset
        latoffset = distancemeters * latdegpermeter * math.cos(anglerad)
        lonoffset = distancemeters * londegpermeter * math.sin(anglerad)
        
        # Calculate new coordinates
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
            "valuefactor": self.AREA_VALUE_FACTORS.get(areaname, 1.0)
        }
    
    def generate_synchronized_locations(self, count: int) -> List[Dict]:
        """
        Generate a list of locations near the Thames with elevation data.
        
        Args:
            count: Number of locations to generate
            
        Returns:
            List of location dictionaries with elevation information
        """
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
                "valuefactor": self.AREA_VALUE_FACTORS.get(areaname, 1.0)
            })
        
        # If more locations needed than gauge points, generate additional random ones
        if count > len(self.GAUGE_POINTS):
            for _ in range(len(self.GAUGE_POINTS), count):
                locations.append(self.calculate_location_near_thames())
        
        return locations
    
    def get_thames_elevation_at_point(self, pointidx: int) -> float:
        """
        Get the elevation at a specific Thames gauge point.
        
        Args:
            pointidx: Index of the Thames point (0-39)
            
        Returns:
            Elevation in meters
        """
        if 0 <= pointidx < len(self.GAUGE_POINTS):
            return self.GAUGE_POINTS[pointidx][2]
        else:
            raise IndexError(f"Thames point index {pointidx} out of range (0-{len(self.GAUGE_POINTS)-1})")
    
    def get_streets_for_area(self, areaname: str) -> List[str]:
        """
        Get street names for a given area.
        
        Args:
            areaname: Name of the London area
            
        Returns:
            List of street names (empty if area not found)
        """
        return self.STREETS.get(areaname, [])
