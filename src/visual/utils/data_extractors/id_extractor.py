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

"""ID extraction utilities for tooltips and popups."""

import re
from typing import Optional


def extract_id_from_tooltip(tooltip_text: str, id_type: str = 'property') -> Optional[str]:
    """
    Extract property or gauge ID from tooltip text.

    Args:
        tooltip_text: Tooltip text content
        id_type: Type of ID to extract ('property' or 'gauge')

    Returns:
        Extracted ID or None if not found
    """
    if not tooltip_text:
        return None

    if id_type == 'property':
        # Look for "Property: XXXXX" pattern
        match = re.search(r'Property:\s*([^|]+)', tooltip_text)
        if match:
            return match.group(1).strip()

    elif id_type == 'gauge':
        # Look for "Gauge: XXXXX" or "GAUGE-XXXXX" pattern
        match = re.search(r'Gauge:\s*([^|]+)', tooltip_text)
        if match:
            return match.group(1).strip()

        # Alternative pattern for direct gauge ID
        match = re.search(r'GAUGE-[a-f0-9]+', tooltip_text)
        if match:
            return match.group(0).strip()

    return None


def extract_id_from_popup(popup_content: str, id_type: str = 'property') -> Optional[str]:
    """
    Extract property or gauge ID from popup content.

    Args:
        popup_content: Popup HTML content
        id_type: Type of ID to extract ('property' or 'gauge')

    Returns:
        Extracted ID or None if not found
    """
    if not popup_content:
        return None

    # Convert to string if needed
    content_string = str(popup_content)

    if id_type == 'property':
        # Look for "ID: XXXXX" pattern in the popup HTML
        match = re.search(r'ID:\s*([^<\r\n]+)', content_string)
        if match:
            return match.group(1).strip()

    elif id_type == 'gauge':
        # Look for "ID: GAUGE-XXXXX" pattern
        match = re.search(r'ID:\s*(GAUGE-[a-f0-9]+)', content_string)
        if match:
            return match.group(1).strip()

        # Alternative: Look for just "GAUGE-XXXXX" pattern
        match = re.search(r'GAUGE-[a-f0-9]+', content_string)
        if match:
            return match.group(0).strip()

    return None
