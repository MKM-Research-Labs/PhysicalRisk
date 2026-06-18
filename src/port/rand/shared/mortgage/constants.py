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

"""Thames mortgage constants — UK market specific."""

from config.port import MORTGAGE_TYPE_WEIGHTS, RATE_TYPE_WEIGHTS  # noqa: F401

UK_LENDERS = [
    "HSBC", "Barclays", "NatWest", "Lloyds", "Santander",
    "Nationwide", "Halifax", "Royal Bank of Scotland",
    "Yorkshire Building Society", "Coventry Building Society"
]

MORTGAGE_TYPES = [
    "Residential", "Buy-to-Let", "Second Home",
    "Holiday Home", "Shared Ownership"
]
# MORTGAGE_TYPE_WEIGHTS imported from config/port.py

RATE_TYPES = [
    "Fixed", "Variable", "Tracker", "Discount",
    "Capped", "Standard Variable Rate"
]
# RATE_TYPE_WEIGHTS imported from config/port.py

REPAYMENT_TYPES = ["Repayment", "Interest only", "Part and part"]
EMPLOYMENT_TYPES = ["Employed", "Self-employed", "Retired", "Unemployed", "Director", "Contractor"]
