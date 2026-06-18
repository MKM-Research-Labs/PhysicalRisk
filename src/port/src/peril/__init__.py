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

"""Peril timeseries derivation — win / faw / fow scenario inputs.

The win (wind-only), faw (flood-AND-wind) and fow (flood-OR-wind) hazard
curves follow the same shd/she scenario protocol as the flood spine: each
mode reads a per-asset timeseries directory and the existing hazard-curve
generator prices it unchanged. This package builds those input dirs by
re-stamping the flood timeseries with the peril outcome.
"""

from .peril_ts import PerilTimeseriesGenerator
from ._commercial import CommercialPerilTimeseriesGenerator

__all__ = ["PerilTimeseriesGenerator", "CommercialPerilTimeseriesGenerator"]
