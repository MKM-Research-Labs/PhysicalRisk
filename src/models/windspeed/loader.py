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

"""Event loader — read an EVT-*.json file produced by the typhoon pipeline
and return a TyphoonTrajectory. Reusable summary-field stripping for
backward compatibility with future format additions.
"""

import json
from pathlib import Path
from typing import Union

from models.typhoon.data_structures import TyphoonTrajectory


__all__ = ["load_event"]


def load_event(source: Union[Path, str, TyphoonTrajectory]) -> TyphoonTrajectory:
    """Return a TyphoonTrajectory from a path, JSON string, or in-memory object.

    Args:
        source: a Path / string pointing to an EVT-*.json file, OR an
            already-instantiated TyphoonTrajectory (pass-through). Accepting
            both lets callers cache events once and reuse them.

    Returns:
        TyphoonTrajectory ready for state interpolation.
    """
    if isinstance(source, TyphoonTrajectory):
        return source

    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Event file not found: {path}")
    with path.open() as f:
        payload = json.load(f)

    # The pipeline's write_event_trajectory adds a 'summary' header for
    # quick inspection. TyphoonTrajectory.from_dict only consumes the
    # core fields; the summary is metadata.
    if "summary" in payload:
        payload = {k: v for k, v in payload.items() if k != "summary"}
    return TyphoonTrajectory.from_dict(payload)
