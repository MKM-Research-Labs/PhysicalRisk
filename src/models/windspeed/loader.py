# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
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
