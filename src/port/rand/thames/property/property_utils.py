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

"""
Utility generators for Thames property random data.

Small helper functions: dates, names, construction years, property periods.
"""

import random
from datetime import datetime, timedelta


def generate_postcode() -> str:
    """Generate a UK-style postcode."""
    area_code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))
    district = random.randint(1, 99)
    sector = random.randint(1, 9)
    unit = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2))
    return f"{area_code}{district} {sector}{unit}"


def generate_construction_year() -> int:
    """Generate a realistic construction year based on era distribution."""
    era = random.choices(
        ['pre-1900', '1900-1950', '1950-1980', '1980-2000', 'post-2000'],
        weights=[0.1, 0.2, 0.3, 0.25, 0.15]
    )[0]

    if era == 'pre-1900':
        return random.randint(1800, 1900)
    elif era == '1900-1950':
        return random.randint(1900, 1950)
    elif era == '1950-1980':
        return random.randint(1950, 1980)
    elif era == '1980-2000':
        return random.randint(1980, 2000)
    else:
        return random.randint(2000, 2022)


def generate_past_date(days_range=(30, 365)) -> str:
    """Generate a past date within specified range."""
    days_ago = random.randint(days_range[0], days_range[1])
    past_date = datetime.now() - timedelta(days=days_ago)
    return past_date.strftime('%Y-%m-%d')


def generate_owner_name() -> str:
    """Generate a realistic previous owner name."""
    first_names = ['John', 'Jane', 'David', 'Johnny', 'Fearghal', 'Sarah', 'Michael', 'Emma', 'James', 'Lisa', 'Robert', 'Anna']
    last_names = ['Smith', 'Johnson', 'Mattimore', 'Kelly', 'Mcgoveran', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
    return f"{random.choice(first_names)} {random.choice(last_names)}"


def get_property_period(construction_year: int) -> str:
    """Get property period classification based on construction year."""
    if construction_year < 1919:
        return "Pre-1919"
    elif construction_year < 1945:
        return "1919-1944"
    elif construction_year < 1976:
        return "1945-1975"
    elif construction_year < 2000:
        return "1976-1999"
    elif construction_year < 2009:
        return "2000-2008"
    else:
        return "2009-Present"


def generate_grid_reference(lat: float, lon: float) -> str:
    """Generate a simplified OS Grid Reference."""
    letters = ['TQ', 'TL', 'SU', 'SK', 'SP', 'SZ']
    numbers = f"{random.randint(10000, 99999)}{random.randint(10000, 99999)}"
    return f"{random.choice(letters)}{numbers}"
