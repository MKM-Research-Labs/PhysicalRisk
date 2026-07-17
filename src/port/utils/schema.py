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
