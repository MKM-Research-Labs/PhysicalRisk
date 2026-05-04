# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
# (see package __init__.py for full license text)

"""
Top-level re-export of the admin-password decorator.

The decorator itself lives at ``src/routes/trading/_admin_auth.py`` because
it was introduced for the Trading Desk Control tab. As admin-gating spreads
to other blueprints (PRS commit, governance if/when needed, etc.), this
shim provides a blueprint-agnostic import path:

    from routes._admin_auth import require_admin_password

The existing trading-scoped import continues to work unchanged so the
downstream test fixture in ``tests/routes/trading/test_control_routes.py``
that monkeypatches ``routes.trading._admin_auth._admin_file_path`` is
unaffected.
"""

from .trading._admin_auth import (  # noqa: F401
    _admin_file_path,
    require_admin_password,
)
