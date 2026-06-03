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
Loan Pricer panel package.

Splits the former single ``property/loanpricer.py`` module into:

- panel:    ``LoanPricerPanel`` Python handler (parameterise + inject JS)
- template: the large client-side JS/HTML body as a ``str.format`` template

``LoanPricerPanel`` is re-exported here so existing imports
(``from visual.interactivity.property.loanpricer import LoanPricerPanel``)
keep working unchanged.
"""

from .panel import LoanPricerPanel
from .template import LOAN_PRICER_JS_TEMPLATE

__all__ = [
    "LoanPricerPanel",
    "LOAN_PRICER_JS_TEMPLATE",
]
