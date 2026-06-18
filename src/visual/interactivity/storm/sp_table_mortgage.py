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
Storm portfolio Table tab — Loan/Mortgage sub-tab JS.

Combined debt view across residential mortgages and commercial loans.
Flood damage and wind damage are summed per asset (capped at the asset
value) and the resulting post-damage value is used to recompute LTV.
Both flood and wind damage are sourced live from the per-storm impact
endpoints; the Wind side is empty when the storm has no typhoon link.
"""

from visual.interactivity._jsbundle import js_static


def get_js() -> str:
    """Return JS fragment for the Loan/Mortgage sub-tab (parent IIFE scope)."""
    return js_static('storm/sp_table_mortgage.js')
