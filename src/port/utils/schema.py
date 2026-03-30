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
