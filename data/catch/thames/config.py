# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# 
# This software is provided under license by MKM Research Labs. 
# Use, reproduction, distribution, or modification of this code is subject to the 
# terms and conditions of the license agreement provided with this software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Thames catchment definition for the Thames River, UK.

This module provides the complete Thames catchment configuration including
gauge points along the Thames from Reading to the estuary, London area
definitions, and property value factors.

The Thames is the primary reference catchment for the PRS platform, with
extensive flood risk modelling and property portfolio analysis.

Gauge coverage (52 points, ordered west to east / upstream to downstream):
  - Upstream non-tidal reach: Reading → Teddington Lock (12 gauges)
  - Tidal Thames, inner London: Richmond → Purfleet (40 gauges)

Teddington Lock (gauge index 11) is the tidal limit of the Thames — the
boundary between the fresh-water managed reach and the tidal estuary.

Usage:
    # Module-level access (for backward compatibility with port.params)
    from catchments import thames
    print(thames.GAUGE_POINTS[0])
    print(thames.CENTER_LAT)

    # Class instance access (for methods)
    catchment = thames.ThamesCatchment()
    locations = catchment.generate_synchronized_locations(200)
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
GAUGE_POINTS = [
    # --- Upstream non-tidal reach ---
    (51.4624, -0.9622, 42.00),  #  0 Reading / Caversham Bridge
    (51.5348, -0.8998, 38.20),  #  1 Henley-on-Thames
    (51.5723, -0.7742, 33.80),  #  2 Marlow Bridge
    (51.5575, -0.7227, 30.50),  #  3 Cookham
    (51.5098, -0.6835, 27.20),  #  4 Maidenhead Bridge
    (51.4839, -0.6077, 24.50),  #  5 Windsor / Eton Bridge
    (51.4325, -0.5087, 22.00),  #  6 Staines Bridge
    (51.3818, -0.5003, 20.10),  #  7 Chertsey Bridge
    (51.3882, -0.4157, 18.20),  #  8 Walton Bridge
    (51.4034, -0.3413, 16.50),  #  9 Hampton Court Bridge
    (51.4104, -0.3075, 15.00),  # 10 Kingston Bridge
    (51.4238, -0.3309, 13.80),  # 11 Teddington Lock (tidal limit)
    # --- Tidal Thames ---
    (51.4573, -0.3072, 11.13), (51.4600, -0.3032, 10.86),
    (51.4724, -0.2686, 10.44), (51.4709, -0.2636, 10.01),
    (51.4723, -0.2546, 9.91), (51.4752, -0.2246, 9.04),
    (51.4882, -0.2304, 8.01), (51.4741, -0.2236, 7.91),
    (51.4669, -0.2131, 7.81), (51.4641, -0.1982, 7.71),
    (51.4720, -0.1800, 7.61), (51.4834, -0.1581, 7.51),
    (51.4844, -0.1442, 7.41), (51.4843, -0.1347, 7.31),
    (51.4900, -0.1250, 7.21), (51.5006, -0.1218, 7.11),
    (51.5098, -0.1104, 7.01), (51.5063, -0.1203, 6.91),
    (51.5099, -0.1049, 6.81), (51.5099, -0.1044, 6.71),
    (51.5092, -0.0954, 6.61), (51.5079, -0.0878, 6.51),
    (51.5055, -0.0753, 6.41), (51.5024, -0.0653, 6.31),
    (51.5030, -0.0544, 6.21), (51.4970, -0.0302, 6.11),
    (51.4939, -0.0291, 6.01), (51.4910, -0.0048, 5.91),
    (51.4896, -0.0007, 5.81), (51.4855, -0.0069, 5.71),
    (51.4872, -0.0029, 5.61), (51.4960, 0.0278, 5.51),
    (51.4969, 0.0368, 5.41), (51.4965, 0.0574, 5.31),
    (51.4971, 0.0693, 5.21), (51.4988, 0.0758, 5.11),
    (51.4854, 0.1851, 5.01), (51.4842, 0.1963, 4.91),
    (51.4707, 0.2442, 4.81), (51.4581, 0.2855, 4.00),
]

# London and upstream Thames areas
AREAS = [
    # Upstream non-tidal (12)
    "Reading", "Henley", "Marlow", "Cookham",
    "Maidenhead", "Windsor", "Staines", "Chertsey",
    "Walton", "Hampton", "Kingston", "Teddington",
    # Tidal Thames (30 — existing)
    "Chelsea", "Kensington", "Westminster", "Camden", "Islington",
    "Hackney", "Tower Hamlets", "Southwark", "Lambeth", "Wandsworth",
    "Greenwich", "Lewisham", "Hammersmith", "Fulham", "Richmond",
    "Newham", "Barking", "Dagenham", "Havering", "Bexley",
    "Tilbury", "Thurrock", "Grays", "Purfleet", "Dartford",
    "Erith", "Belvedere", "Thamesmead", "Abbey Wood", "Woolwich"
]

# Gauge short names: one per GAUGE_POINTS entry (52 total), ordered west to east
# These are real Thames-side locations matching the gauge coordinates
GAUGE_NAMES = [
    # Upstream non-tidal reach (indices 0-11)
    "Caversham Bridge",     #  0 (-0.9622) Reading
    "Marsh Lock",           #  1 (-0.8998) Henley-on-Thames
    "Marlow Bridge",        #  2 (-0.7742) Marlow
    "Cookham Bridge",       #  3 (-0.7227) Cookham
    "Maidenhead Bridge",    #  4 (-0.6835) Maidenhead
    "Windsor Bridge",       #  5 (-0.6077) Windsor / Eton
    "Staines Bridge",       #  6 (-0.5087) Staines-upon-Thames
    "Chertsey Bridge",      #  7 (-0.5003) Chertsey
    "Walton Bridge",        #  8 (-0.4157) Walton-on-Thames
    "Hampton Court Bridge", #  9 (-0.3413) Hampton Court
    "Kingston Bridge",      # 10 (-0.3075) Kingston-upon-Thames
    "Teddington Lock",      # 11 (-0.3309) Tidal limit
    # Tidal Thames (indices 12-51)
    "Richmond Lock",        # 12 (-0.3072) Richmond
    "Richmond Bridge",      # 13 (-0.3032)
    "Kew Bridge",           # 14 (-0.2686)
    "Kew Gardens",          # 15 (-0.2636)
    "Chiswick Bridge",      # 16 (-0.2546)
    "Barnes Bridge",        # 17 (-0.2246)
    "Hammersmith Bridge",   # 18 (-0.2304)
    "Putney Bridge",        # 19 (-0.2236)
    "Wandsworth Bridge",    # 20 (-0.2131)
    "Battersea Bridge",     # 21 (-0.1982)
    "Chelsea Bridge",       # 22 (-0.1800)
    "Vauxhall Bridge",      # 23 (-0.1581)
    "Lambeth Bridge",       # 24 (-0.1442)
    "Westminster Bridge",   # 25 (-0.1347)
    "Hungerford Bridge",    # 26 (-0.1250)
    "Waterloo Bridge",      # 27 (-0.1218)
    "Blackfriars Bridge",   # 28 (-0.1104)
    "Millennium Bridge",    # 29 (-0.1203)
    "Southwark Bridge",     # 30 (-0.1049)
    "Cannon Street",        # 31 (-0.1044)
    "London Bridge",        # 32 (-0.0954)
    "Tower Bridge",         # 33 (-0.0878)
    "Wapping",              # 34 (-0.0753)
    "Rotherhithe",          # 35 (-0.0653)
    "Limehouse",            # 36 (-0.0544)
    "Isle of Dogs",         # 37 (-0.0302)
    "Deptford Creek",       # 38 (-0.0291)
    "Greenwich Pier",       # 39 (-0.0048)
    "Greenwich Reach",      # 40 (-0.0007)
    "Blackwall",            # 41 (-0.0069)
    "Blackwall Tunnel",     # 42 (-0.0029)
    "Silvertown",           # 43 (0.0278)
    "Royal Victoria Dock",  # 44 (0.0368)
    "Royal Albert Dock",    # 45 (0.0574)
    "King George V Dock",   # 46 (0.0693)
    "Woolwich Ferry",       # 47 (0.0758)
    "Barking Creek",        # 48 (0.1851)
    "Dagenham Dock",        # 49 (0.1963)
    "Rainham Marshes",      # 50 (0.2442)
    "Purfleet",             # 51 (0.2855)
]

# Street names by area for address generation
STREETS = {
    # Upstream non-tidal reach
    "Reading": [
        "Caversham Road", "Bridge Street", "Kings Road", "London Street",
        "Oxford Road", "Friar Street", "Queens Road"
    ],
    "Henley": [
        "Hart Street", "Bell Street", "Duke Street", "Market Place",
        "Friday Street", "Gravel Hill", "Reading Road"
    ],
    "Marlow": [
        "High Street", "West Street", "Station Road", "Pound Lane",
        "Oxford Road", "Spittal Street", "Dedmere Road"
    ],
    "Cookham": [
        "High Street", "Cookham Road", "Maidenhead Road", "Mill Lane",
        "Lower Road", "Church Gate", "Station Road"
    ],
    "Maidenhead": [
        "High Street", "Bridge Road", "King Street", "Queen Street",
        "Boyn Valley Road", "Ray Mill Road", "Cookham Road"
    ],
    "Windsor": [
        "High Street", "Peascod Street", "Sheet Street", "St Leonard's Road",
        "Frances Road", "Victoria Street", "Thames Street"
    ],
    "Staines": [
        "High Street", "Church Street", "Kingston Road", "Clarence Street",
        "Gresham Road", "Laleham Road", "Stanwell Road"
    ],
    "Chertsey": [
        "Bridge Road", "Guildford Street", "Windsor Street", "London Street",
        "Free Prae Road", "Heriot Road", "Chilsey Green Road"
    ],
    "Walton": [
        "Bridge Street", "High Street", "Manor Road", "Hersham Road",
        "Terrace Road", "Ashley Road", "Halfway"
    ],
    "Hampton": [
        "High Street", "Thames Street", "Station Road", "Park Road",
        "Church Street", "Ripley Road", "Uxbridge Road"
    ],
    "Kingston": [
        "High Street", "Thames Street", "Eden Street", "Clarence Street",
        "Richmond Road", "Kings Passage", "Market Place"
    ],
    "Teddington": [
        "High Street", "Broad Street", "Park Road", "Station Road",
        "Twickenham Road", "Kingston Road", "Sandy Lane"
    ],
    # Tidal Thames
    "Chelsea": [
        "Kings Road", "Cheyne Walk", "Royal Avenue", "Sloane Square",
        "Flood Street", "Beaufort Street", "Chelsea Embankment"
    ],
    "Kensington": [
        "Kensington High Street", "Holland Park", "Pembroke Road",
        "Kensington Court", "Campden Hill Road", "Phillimore Gardens"
    ],
    "Westminster": [
        "Victoria Street", "Whitehall", "Birdcage Walk", "Great Smith Street",
        "Millbank", "Horseferry Road", "Page Street"
    ],
    "Camden": [
        "Camden High Street", "Parkway", "Chalk Farm Road", "Delancey Street",
        "Arlington Road", "Jamestown Road"
    ],
    "Islington": [
        "Upper Street", "Liverpool Road", "Essex Road", "Canonbury Square",
        "St Peters Street", "Cross Street"
    ],
    "Hackney": [
        "Mare Street", "Broadway Market", "Kingsland Road", "Dalston Lane",
        "Graham Road", "Morning Lane"
    ],
    "Tower Hamlets": [
        "Commercial Road", "Brick Lane", "Cable Street", "Roman Road",
        "Mile End Road", "Whitechapel Road"
    ],
    "Southwark": [
        "Borough High Street", "Long Lane", "Tower Bridge Road", "Bermondsey Street",
        "Tooley Street", "Jamaica Road"
    ],
    "Lambeth": [
        "Kennington Road", "Lambeth Road", "Albert Embankment", "Camberwell New Road",
        "Brixton Road", "Westminster Bridge Road"
    ],
    "Wandsworth": [
        "Wandsworth High Street", "East Hill", "Trinity Road", "Lavender Hill",
        "Battersea Park Road", "York Road"
    ],
    "Greenwich": [
        "Greenwich High Road", "Trafalgar Road", "Woolwich Road", "Creek Road",
        "Blackwall Lane", "Tunnel Avenue"
    ],
    "Lewisham": [
        "Lewisham High Street", "Lee High Road", "Loampit Vale", "Rushey Green",
        "Brownhill Road", "Catford Road"
    ],
    "Hammersmith": [
        "King Street", "Hammersmith Road", "Shepherds Bush Road", "Fulham Palace Road",
        "Glenthorne Road", "Beadon Road"
    ],
    "Fulham": [
        "Fulham Road", "New Kings Road", "Lillie Road", "North End Road",
        "Munster Road", "Parsons Green Lane"
    ],
    "Richmond": [
        "George Street", "Hill Street", "The Quadrant", "Kew Road",
        "Sheen Road", "Paradise Road"
    ]
}

# Property value factors by London area (multiplier of base value)
AREA_VALUE_FACTORS = {
    # Upstream non-tidal reach
    'Reading': 0.9, 'Henley': 1.1, 'Marlow': 1.2, 'Cookham': 1.1,
    'Maidenhead': 1.0, 'Windsor': 1.3, 'Staines': 0.9, 'Chertsey': 0.9,
    'Walton': 1.1, 'Hampton': 1.2, 'Kingston': 1.3, 'Teddington': 1.3,
    # Tidal Thames
    'Chelsea': 2.0, 'Kensington': 1.9, 'Westminster': 1.8,
    'Camden': 1.5, 'Islington': 1.4, 'Hackney': 1.2,
    'Tower Hamlets': 1.3, 'Southwark': 1.2, 'Lambeth': 1.1,
    'Wandsworth': 1.4, 'Greenwich': 1.3, 'Lewisham': 1.1,
    'Hammersmith': 1.5, 'Fulham': 1.4, 'Richmond': 1.6,
    'Newham': 1.0, 'Barking': 0.9, 'Dagenham': 0.8,
    'Havering': 0.9, 'Bexley': 0.9, 'Tilbury': 0.7,
    'Thurrock': 0.8, 'Grays': 0.7, 'Purfleet': 0.8,
    'Dartford': 0.9, 'Erith': 0.8, 'Belvedere': 0.8,
    'Thamesmead': 0.9, 'Abbey Wood': 0.9, 'Woolwich': 1.0
}

# UK flood decision bodies
FLOOD_DECISION_BODIES = [
    "Environment Agency",
    "Department for Environment, Food and Rural Affairs",
    "Natural Resources Wales",
    "Scottish Environment Protection Agency"
]

# Gauge owners in Thames region
GAUGE_OWNERS = [
    "Environment Agency",
    "Thames Water",
    "Local Authority",
    "Met Office",
    "Research Institution"
]

# Data curators
DATA_CURATORS = [
    "Environment Agency",
    "Met Office",
    "CEDA Archive",
    "British Hydrological Society",
    "Centre for Ecology & Hydrology"
]

# UK mortgage lenders
MORTGAGE_LENDERS = [
    "HSBC", "Barclays", "NatWest", "Lloyds", "Santander",
    "Nationwide", "Halifax", "Royal Bank of Scotland",
    "Yorkshire Building Society", "Coventry Building Society"
]

# Geographic bounds (min_lon, min_lat, max_lon, max_lat)
BOUNDS = (-0.35, 51.41, 0.38, 51.52)

# Center point for Thames catchment (approximate center of London/Thames)
CENTER_LAT = 51.5074
CENTER_LON = -0.1278

# Base property value in GBP
BASE_PROPERTY_VALUE = 500000

# Elevation model parameters
MAXSLOPEPERCENT = 2.0
MAXRANDOMELEVATION = 10.0


# =============================================================================
# THAMES CATCHMENT CLASS
# =============================================================================

class ThamesCatchment(BaseCatchment):
    """
    Thames River catchment covering Reading to the Thames Estuary.

    The Thames catchment includes 52 gauge points: 12 upstream non-tidal
    gauges (Reading to Teddington Lock) and 40 tidal Thames gauges
    (Richmond Lock to Purfleet). Property values in the Thames floodplain
    exceed £80 billion.
    """
    
    # Expose module-level constants as class attributes
    NAME = "thames"
    REGION = "Europe"
    DISPLAYNAME = "Thames"
    COUNTRY = "UK"
    
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