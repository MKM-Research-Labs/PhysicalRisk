#!/usr/bin/env python3

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

"""
Add missing __init__.py files to test subdirectories.

Based on diagnostic, we need __init__.py in:
- tests/other/
- tests/port/
"""

from pathlib import Path

PROJECT_ROOT = Path.cwd()

DIRS_NEEDING_INIT = [
    'tests/other',
    'tests/port',
]


def create_init(directory: str):
    """Create __init__.py in directory if it doesn't exist."""
    dir_path = PROJECT_ROOT / directory

    if not dir_path.exists():
        print(f"Skipping {directory}/ - directory doesn't exist")
        return

    init_file = dir_path / '__init__.py'

    if init_file.exists():
        print(f"{directory}/__init__.py already exists")
        return

    with open(init_file, 'w') as f:
        f.write(f'"""Test package: {dir_path.name}"""\n')

    print(f"Created {directory}/__init__.py")


def main():
    print("=" * 60)
    print("  Adding Missing __init__.py Files")
    print("=" * 60)

    for directory in DIRS_NEEDING_INIT:
        create_init(directory)

    print("=" * 60)
    print("  Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
