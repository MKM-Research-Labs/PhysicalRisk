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

"""The app builds the way ``phys.py server`` builds it, not only under pytest.

pytest's conftest puts the repo root and ``src/`` at the front of ``sys.path``,
so ``from src.models...`` resolves in tests. Under the CLI it does not:
``config`` adds every source dir to ``sys.path``, including ``src/port``, whose
own ``src/`` package then shadows the repo's. A route importing ``src.models``
passed every test and still killed ``phys.py server`` at start-up.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC = PROJECT_ROOT / "src"

# What cmd_server does up to create_app(), with phys.py's sys.path (cwd first).
_BUILD_LIKE_THE_CLI = """
import os
from app.cli import build_parser  # noqa: F401  (phys.py's first import)
from config import config
with config.use_catchment(os.environ.get("MKM_CATCHMENT") or "thames"):
    from server import create_app
    create_app()
print("CREATE_APP_OK")
"""

_SRC_PREFIXED_IMPORT = re.compile(r"^\s*(from|import)\s+src\.", re.MULTILINE)


def test_no_module_under_src_imports_via_the_src_package():
    """Code under src/ imports as ``models...``, never ``src.models...``."""
    offenders = [
        str(p.relative_to(PROJECT_ROOT))
        for p in SRC.rglob("*.py")
        if "__pycache__" not in p.parts
        and _SRC_PREFIXED_IMPORT.search(p.read_text(encoding="utf-8", errors="ignore"))
    ]
    assert offenders == [], f"src.-prefixed imports break phys.py server: {offenders}"


def test_create_app_builds_with_the_cli_sys_path():
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    result = subprocess.run(
        [sys.executable, "-c", _BUILD_LIKE_THE_CLI],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert "CREATE_APP_OK" in result.stdout, (
        f"create_app() failed under the CLI's sys.path (rc={result.returncode}):\n"
        f"{result.stderr[-4000:]}"
    )
