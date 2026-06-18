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
Loan/mortgage asset CDM package.

Splits the former single ``asset/loan.py`` module into focused sub-modules:

- schema:  ``MORTGAGE_SCHEMA`` dict + ``_unwrap_loan`` / ``_loan_id`` helpers
- cdm:     ``LoanCDM`` class (validate / create_mapping / to_pricer_inputs)

The public names are re-exported here so existing imports
(``from port.cdm.asset.loan import LoanCDM`` /
``from port.cdm.asset.loan import MORTGAGE_SCHEMA``) keep working unchanged.
"""

from .cdm import LoanCDM
from .schema import MORTGAGE_SCHEMA, _loan_id, _unwrap_loan

__all__ = [
    "LoanCDM",
    "MORTGAGE_SCHEMA",
    "_loan_id",
    "_unwrap_loan",
]
