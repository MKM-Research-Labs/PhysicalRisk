# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""Combined JS fragment for the model-governance detail tab renderers."""

from .overview import get_overview_js
from .tables import get_tables_js
from .version_history import get_version_history_js
from .docs import get_docs_js
from .helpers import get_helpers_js


def get_js():
    """Return JS fragment for detail tab renderers."""
    return (get_helpers_js() +
            get_overview_js() +
            get_tables_js() +
            get_version_history_js() +
            get_docs_js())
