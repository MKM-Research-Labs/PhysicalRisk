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
Property valuation and insurance premium models.
"""

from models.valuation.insurance import (
    FLOOD_RISK_PREMIUM_FACTORS,
    PROPERTY_TYPE_PREMIUM_FACTORS,
    apply_insurance_factors,
)
from models.valuation.property_value import (
    AGE_BAND_FACTORS,
    BASE_AREA_RANGES,
    BASE_PRICE_PER_SQM,
    CONDITION_FACTORS,
    EPC_FACTORS,
    FLOOD_RISK_FACTORS,
    apply_valuation_factors,
)

__all__ = [
    'BASE_AREA_RANGES', 'BASE_PRICE_PER_SQM',
    'AGE_BAND_FACTORS', 'CONDITION_FACTORS',
    'FLOOD_RISK_FACTORS', 'EPC_FACTORS',
    'apply_valuation_factors',
    'FLOOD_RISK_PREMIUM_FACTORS', 'PROPERTY_TYPE_PREMIUM_FACTORS',
    'apply_insurance_factors',
]
