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

"""Canonical JSON serialization for the database package.

The whole codebase hands raw payloads to ``save_*`` — including ``datetime`` and
numpy scalars/arrays that plain :func:`json.dumps` cannot encode. This module owns
the one encoder used for every document write so callers never pass their own
(it mirrors ``port.utils.encoders.DateTimeEncoder``: ``datetime`` → ISO-8601,
numpy → native Python). Keeping it here means the Postgres backend can reuse the
identical rule when it serializes to JSONB.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any


def json_default(obj: Any):
    """``default`` hook for :func:`json.dumps` — mirrors the port DateTimeEncoder.

    ``datetime``/``date`` serialize to ISO-8601; numpy scalars and arrays serialize
    to native Python via their ``tolist`` method (``np.int64`` → ``int``,
    ``np.float64`` → ``float``, ``np.ndarray`` → ``list``). Anything else raises, as
    the default encoder would. numpy is duck-typed so the package stays dependency-free.
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    tolist = getattr(obj, "tolist", None)
    if callable(tolist):
        return tolist()
    raise TypeError(
        f"Object of type {type(obj).__name__} is not JSON serializable")


def dumps(payload: Any) -> str:
    """Serialize a document payload exactly as the file backend writes it."""
    return json.dumps(payload, indent=2, default=json_default)
