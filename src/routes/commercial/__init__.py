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

"""Commercial-asset routes package.

Splits the former single ``routes/commercial.py`` module into focused
sub-modules that all register on one shared blueprint:

- reports:   PDF report + loan-report endpoints
- pricing:   loan-pricer endpoint
- storms:    storm-scenario endpoint + catchment enrichment helpers
- hazard:    hazard-curve (hc/she/shd/bri) + asset-record endpoints
- portfolio: list / blotter / per-storm portfolio-impact endpoints

``commercial_bp`` is re-exported so ``routes.registry`` can keep doing
``from .commercial import commercial_bp`` unchanged.
"""

from .blueprint import commercial_bp  # noqa: F401

# Import sub-modules to register their routes on commercial_bp.
from . import reports    # noqa: E402, F401
from . import pricing    # noqa: E402, F401
from . import storms     # noqa: E402, F401
from . import hazard     # noqa: E402, F401
from . import portfolio  # noqa: E402, F401
