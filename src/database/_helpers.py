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

"""Private helpers shared by the public-API submodules."""

from __future__ import annotations

from typing import Any

from config.data_layout import DEFAULT_MODE, ID_FIELDS

from .backend import active_backend


def load_or(artifact, catchment, key=None, *, mode=DEFAULT_MODE, default=None):
    """Load one record, translating 'absent' into ``default`` not an exception."""
    try:
        return active_backend().load(artifact, catchment, key, mode=mode)
    except (FileNotFoundError, KeyError):
        return default


def records(doc: Any) -> list:
    """Normalise a portfolio document to a list of records, whether it is a bare list
    or a dict that wraps one (e.g. ``{"properties": [...]}``)."""
    if isinstance(doc, list):
        return doc
    if isinstance(doc, dict):
        for value in doc.values():
            if isinstance(value, list):
                return value
    return []


def matches(record: Any, entity_id: str) -> bool:
    return isinstance(record, dict) and any(
        record.get(field) == entity_id for field in ID_FIELDS)


def list_records(artifact, catchment) -> list:
    return records(load_or(artifact, catchment, default=[]))


def find_record(artifact, catchment, entity_id):
    return next(
        (r for r in list_records(artifact, catchment) if matches(r, entity_id)), None)
