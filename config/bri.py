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
BRI (Building Resilience Index) resilience parameters.

Defaults for the property-resilience model and its synthetic-checklist
generator. The BRI *shift* coefficients used by the damage models
(BRI_FLOOD_ALPHA_M, BRI_WIND_REFERENCE, …) live in config/damage.py alongside
the depth-damage curve they modify.
"""

# Default 0-1 compliance for a missing resilience value
# (spec recommends 0.25 + a confidence penalty).
DEFAULT_MISSING_COMPLIANCE: float = 0.25

# Synthetic property-resilience generation fallbacks: flood-defence adoption
# probability for an unknown construction period, and the condition multiplier
# for an unknown building condition.
RESILIENCE_DEFAULT_PERIOD_PROB: float = 0.40
RESILIENCE_DEFAULT_CONDITION_MULT: float = 1.0
