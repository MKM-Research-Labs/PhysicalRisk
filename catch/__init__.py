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

"""Catchment parameter modules — the vendored, version-controlled home.

A catchment's parameters (``BOUNDS``, ``CURRENCY``, flood thresholds, the
tropical-cyclone exposure in ``tc.py``, the seismic ``fault_trace.json``) are
**inputs to generation**, not outputs of it, and they are configuration rather
than data. They historically lived under ``data/catch/``, which on the
development machine is a symlink to external storage — so with that volume
detached nothing could be generated, and ``config.get_catchment_bounds()``
failed with ``ModuleNotFoundError: No module named 'catch'``.

This package is the preferred home. ``config.project_root`` precedes
``config.data_root`` on ``sys.path``, so a catchment vendored here shadows the
same name under ``data/catch/``; anything not yet migrated still resolves
there, so the move can be done one catchment at a time.

Same argument as the governance data, which was moved out of ``data/`` for
being repo-level content sitting in a shared, per-deployment area.

To migrate a catchment, with the data volume attached:

    cp -R "$(python -c 'from config import config; print(config.data_root)')/catch/thames" catch/
    # or, for a single-file catchment:
    cp "$(...)/catch/thames.py" catch/

then confirm it is being read from here rather than there:

    python -c "import catch.thames as m; print(m.__file__)"
"""
