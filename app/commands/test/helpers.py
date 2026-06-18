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

"""Python-interpreter resolution and worktree data-cleanup helpers."""

import os
import shutil
import subprocess as sp


def _resolve_python(project_root):
    """Return the project venv Python if available, else sys.executable."""
    import sys
    for venv_dir in ('.venv', 'venv'):
        candidate = os.path.join(str(project_root), venv_dir, 'bin', 'python')
        if os.path.isfile(candidate):
            return candidate
    return sys.executable


def _cleanup_worktree_data(project_root: str) -> None:
    """Remove data/input/ copies inside git worktrees (not the main repo).

    E2E tests spin up a Flask subprocess per worktree and write a full copy of
    data/input/<catchment>/ into each worktree's working tree.  Those copies
    are never tracked by git but can easily reach 6-7 GB each and accumulate
    across sessions.  This function wipes them after every test run.
    """
    try:
        result = sp.run(
            ['git', 'worktree', 'list', '--porcelain'],
            capture_output=True, text=True, cwd=project_root,
        )
        if result.returncode != 0:
            return

        # Parse worktree paths — each block starts with "worktree <path>"
        worktree_paths = [
            line[len('worktree '):].strip()
            for line in result.stdout.splitlines()
            if line.startswith('worktree ')
        ]

        freed_bytes = 0
        cleaned = []
        for wt_path in worktree_paths:
            if os.path.realpath(wt_path) == os.path.realpath(project_root):
                continue  # skip main repo

            # CRITICAL: a worktree's `data/` may be a symlink to shared
            # storage (e.g. an external SSD that every checkout points at).
            # Following it would make the rmtree below delete the REAL shared
            # catchment data, not a disposable per-worktree copy.  Skip any
            # worktree whose data dir is a symlink, or whose resolved
            # data/input path escapes the worktree directory.
            wt_data = os.path.join(wt_path, 'data')
            if os.path.islink(wt_data):
                print(f'  Skipping {wt_path}: data/ is a symlink '
                      f'(would follow to shared storage)')
                continue
            data_input = os.path.join(wt_path, 'data', 'input')
            if not os.path.isdir(data_input):
                continue
            wt_real = os.path.realpath(wt_path)
            if not os.path.realpath(data_input).startswith(wt_real + os.sep):
                print(f'  Skipping {data_input}: resolves outside worktree '
                      f'({os.path.realpath(data_input)})')
                continue
            for catchment in os.listdir(data_input):
                catchment_dir = os.path.join(data_input, catchment)
                if not os.path.isdir(catchment_dir):
                    continue
                # Belt-and-braces: never delete through a per-catchment symlink.
                if os.path.islink(catchment_dir):
                    continue
                try:
                    # du -s equivalent using os.walk
                    size = sum(
                        os.path.getsize(os.path.join(dp, f))
                        for dp, _, fns in os.walk(catchment_dir)
                        for f in fns
                    )
                    shutil.rmtree(catchment_dir)
                    freed_bytes += size
                    cleaned.append(f'{wt_path} → data/input/{catchment}')
                except Exception as exc:
                    print(f'  WARNING: could not remove {catchment_dir}: {exc}')

        if cleaned:
            freed_gb = freed_bytes / (1024 ** 3)
            print(f'Worktree data cleanup: removed {len(cleaned)} data copy/copies '
                  f'({freed_gb:.1f} GB freed)')
            for entry in cleaned:
                print(f'  {entry}')
        else:
            print('Worktree data cleanup: nothing to remove.')

    except Exception as exc:
        print(f'WARNING: worktree data cleanup failed: {exc}')
