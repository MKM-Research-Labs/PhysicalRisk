#!/usr/bin/env python3

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

"""
Generate LaTeX parameter inventory for model governance.

Produces a single PDF cataloguing all hard-coded input parameters
across the analytical model codebase.

Usage:
    python -m docs.models.parameter_inventory.generator
    python -m docs.models.parameter_inventory.generator --pdf
"""

import argparse
import os

from config import config

from .parameters import get_parameter_sections
from .latex import generate_document
from .compiler import compile_pdf

_output_dir = str(config.get_project_root() / 'docs' / 'models' / 'parameter_inventory')


def main():
    parser = argparse.ArgumentParser(
        description='Generate LaTeX parameter inventory')
    parser.add_argument('--pdf', action='store_true',
                        help='Compile LaTeX to PDF')
    args = parser.parse_args()

    print('=' * 60)
    print('MKM Research Labs — Parameter Inventory Generator')
    print('=' * 60)
    print()

    # Generate LaTeX
    sections = get_parameter_sections()
    content = generate_document(sections)
    os.makedirs(_output_dir, exist_ok=True)
    tex_path = os.path.join(_output_dir, 'parameter_inventory.tex')

    with open(tex_path, 'w') as f:
        f.write(content)
    print(f'  LaTeX written: {tex_path}')

    if args.pdf:
        compile_pdf(_output_dir, tex_path)

    print('\nDone.')


if __name__ == '__main__':
    main()
