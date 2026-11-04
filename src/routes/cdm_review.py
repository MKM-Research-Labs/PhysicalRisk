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

"""Mount the CDM Asset Review workstream inside the main application.

The tool is its own Flask app (``tools/cdm_property_editor/app.py``) and still
runs standalone on port 5057. Here the same app is mounted at
``/cdm-asset-review/`` so the platform serves it from one origin and one port:
the map's house icon opens it in an in-app panel without a second server.

The tool is imported on the first request under the prefix, not at start-up:
its import binds the data backend and reads the catchment, which the rest of
the platform (and its tests) should not pay for unless the tool is opened.
"""

import importlib.util
import sys
import threading

from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.utils import redirect

from config import config

PREFIX = "/cdm-asset-review"
TOOL_DIR = config.get_project_root() / "tools" / "cdm_property_editor"
# Unique module name: the tool's ``app.py`` must not shadow the repo's ``app``.
MODULE_NAME = "cdm_asset_review_app"


def _load_tool_app():
    """Import the tool's Flask app by file path, as its tests do."""
    if MODULE_NAME in sys.modules:
        return sys.modules[MODULE_NAME].app
    spec = importlib.util.spec_from_file_location(MODULE_NAME, TOOL_DIR / "app.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = mod  # before exec, so Flask(__name__) finds its root
    # app.py imports its siblings (recompute, price_new) by bare name; put the tool
    # dir on the path only for the exec. The siblings stay cached in sys.modules.
    added = str(TOOL_DIR) not in sys.path
    if added:
        sys.path.insert(0, str(TOOL_DIR))
    try:
        spec.loader.exec_module(mod)
    except BaseException:
        sys.modules.pop(MODULE_NAME, None)
        raise
    finally:
        if added:
            sys.path.remove(str(TOOL_DIR))
    return mod.app


class LazyCdmReview:
    """WSGI app that loads the CDM tool on first use and serves it under PREFIX."""

    def __init__(self, loader=_load_tool_app):
        self._loader = loader
        self._app = None
        self._lock = threading.Lock()

    def __call__(self, environ, start_response):
        # The tool's page uses relative URLs, so it must be served at PREFIX + "/".
        if not environ.get("PATH_INFO"):
            return redirect(environ.get("SCRIPT_NAME", "") + "/")(environ, start_response)
        if self._app is None:
            with self._lock:
                if self._app is None:
                    self._app = self._loader()
        return self._app(environ, start_response)


def mount_cdm_review(app, tool=None) -> None:
    """Serve the CDM Asset Review tool at PREFIX on ``app``."""
    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {PREFIX: tool or LazyCdmReview()})
