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
Residential asset CDM package.

Sub-modules
-----------
schema     — PROPERTY_SCHEMA dict + DEFAULT_ELEVATION constant
cdm        — ResidentialAssetCDM class
validator  — validate() and get_required_fields() functions
mapping    — create_mapping() function (nested CDM -> flat snake_case)
bri        — apply_bri_rating() helper
contents   — CONTENTS_SCHEMA (asset.residential-specific extension)
"""

from .cdm import ResidentialAssetCDM  # noqa: F401
from .schema import DEFAULT_ELEVATION, PROPERTY_SCHEMA  # noqa: F401

__all__ = ["ResidentialAssetCDM", "PROPERTY_SCHEMA", "DEFAULT_ELEVATION"]
