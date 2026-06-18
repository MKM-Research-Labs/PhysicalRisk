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

"""Shared predicates for the wind-coupled hazard stages."""

from ...context import StageContext


def _damage_available(ctx: StageContext) -> bool:
    """True when the typhoon damage join input exists for this catchment."""
    damage_dir = ctx.input_dir / "typhoon" / "damage"
    return damage_dir.exists() and any(damage_dir.glob("EVT-*.json"))


def _peril_requested(ctx: StageContext) -> bool:
    a = ctx.args
    return any(getattr(a, f, False) for f in (
        "propertytsw", "propertytsfaw", "propertytsfow",
        "propertytsbow", "propertytsbaw",
        "propertywin", "propertyfaw", "propertyfow",
        "propertybow", "propertybaw",
    ))


def _commercial_peril_requested(ctx: StageContext) -> bool:
    a = ctx.args
    return any(getattr(a, f, False) for f in (
        "commercialtsw", "commercialtsfaw", "commercialtsfow",
        "commercialtsbow", "commercialtsbaw",
        "commercialwin", "commercialfaw", "commercialfow",
        "commercialbow", "commercialbaw",
    ))
