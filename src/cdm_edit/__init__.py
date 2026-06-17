# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see ../auth.py for full license text)

"""Schema-driven editing support for CDM fields.

Turns CDM schema descriptors into editor specs (input widget, menu options,
numeric bounds) and validates/coerces edited values on commit. See
constraints.py (specs) and validate.py (validation).
"""

from .constraints import descriptor_at, field_spec, schema_specs
from .validate import validate_value

__all__ = [
    "field_spec",
    "schema_specs",
    "descriptor_at",
    "validate_value",
]
