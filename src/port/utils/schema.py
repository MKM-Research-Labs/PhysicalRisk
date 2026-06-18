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

"""Shared schema-walking utilities for portfolio builders."""

from typing import Dict


def build_section(section_schema: Dict, index: int, metadata: Dict,
                  random_generator) -> Dict:
    """Recursively build a section of data based on the schema.

    Parameters
    ----------
    section_schema : dict
        The JSON-like schema describing the section.
    index : int
        Zero-based index of the item being generated.
    metadata : dict
        Contextual metadata passed through to the random generator.
    random_generator : object
        An object exposing ``generate_field_value(field_name, field_def,
        index, metadata)`` (e.g. ``GaugeRandomGenerator`` or
        ``PropertyRandomGenerator``).

    Returns
    -------
    dict
        The populated section data.
    """
    result = {}

    if not isinstance(section_schema, dict):
        return {}

    for field_name, field_def in section_schema.items():
        if field_name in ['type', 'options', 'description', 'values']:
            continue

        if isinstance(field_def, dict) and not field_def.get("type"):
            result[field_name] = build_section(field_def, index, metadata,
                                               random_generator)
        else:
            value = random_generator.generate_field_value(
                field_name, field_def, index, metadata)
            if value is not None:
                result[field_name] = value

    return result
