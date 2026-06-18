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

"""Shared rendering helpers for asset report sections.

The render_<section> utilities each build one or more key/value tables
from a section dict. To avoid 30-line "build a Table, set a style,
add a Spacer" blocks repeated nine times, the boilerplate is factored
into :func:`build_kv_table` here. Each section renderer just declares
the (label, value) pairs it wants on each table; everything else is
done in one place.
"""

from typing import Any, Iterable, List, Optional, Sequence, Tuple

from reportlab.platypus import Paragraph, Spacer, Table


def build_kv_table(
    rows: Iterable[Tuple[str, Any]],
    page,
    *,
    header: Tuple[str, str] = ("Field", "Value"),
    style: str = "standard",
    col_widths: str = "two_col",
) -> List:
    """Build a two-column key/value table from (label, value) rows.

    Skips rows whose value is ``None`` or an empty string so the
    resulting table only contains populated fields. Returns an empty
    list if no row survives, so callers can compose unconditionally.

    Args:
        rows: Iterable of (label, value) tuples. Values pass through
            ``page._format_value`` unless already strings — pre-format
            currency, percent, etc. via the page formatters first.
        page: Any ``AssetBasePage`` subclass — supplies styles,
            ``table_styles`` and ``table_widths``.
        header: Two-string header row.
        style: Key in ``page.table_styles``.
        col_widths: Key in ``page.table_widths``.

    Returns:
        ``[Table, Spacer]`` if rows survived, otherwise ``[]``.
    """
    data: List[List[str]] = [list(header)]
    for label, value in rows:
        if value is None:
            continue
        if isinstance(value, str):
            if not value.strip():
                continue
            cell = value
        else:
            cell = page._format_value(value)
        data.append([label, cell])

    if len(data) == 1:
        return []

    table = Table(data, colWidths=page.table_widths[col_widths])
    table.setStyle(page.table_styles[style])
    return [table, Spacer(1, page.spacing["table_bottom"])]


def section_block(
    title: str,
    page,
    rows: Iterable[Tuple[str, Any]],
    *,
    style: str = "standard",
    header_style: str = "SubSectionHeader",
    col_widths: str = "two_col",
    header: Tuple[str, str] = ("Field", "Value"),
) -> List:
    """Convenience: a section header + a key/value table, with spacing.

    Returns an empty list when no rows survive, so caller-side
    ``if has_data`` checks aren't needed.
    """
    table_part = build_kv_table(
        rows, page, header=header, style=style, col_widths=col_widths
    )
    if not table_part:
        return []
    return [
        Paragraph(title, page.styles[header_style]),
        *table_part,
        Spacer(1, page.spacing["minor_section"]),
    ]


def auto_rows(section: dict, mapping: Sequence[Tuple[str, str]]) -> List[Tuple[str, Any]]:
    """Build (label, value) rows by looking up each field key in ``section``.

    ``mapping`` is a sequence of ``(field_key, label)`` tuples. Missing
    keys are skipped silently — same convention as the existing
    property pages.
    """
    return [(label, section.get(key)) for key, label in mapping if section.get(key) is not None]
