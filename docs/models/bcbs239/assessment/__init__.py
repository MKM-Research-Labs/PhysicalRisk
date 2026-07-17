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
Generate BCBS 239 Self-Assessment Report PDF using LaTeX.

Produces a formal self-assessment document scoring the platform against
the 14 BCBS 239 principles for effective risk data aggregation and reporting.

Usage:
    python -m docs.models.bcbs239.assessment
    python -m docs.models.bcbs239.assessment --pdf
"""

import argparse
import os

from config import config

from .data import load_assessment
from .latex import generate_document
from .compiler import compile_pdf

_output_dir = config.get_project_root() / 'docs' / 'models' / 'bcbs239'


def main():
    parser = argparse.ArgumentParser(
        description='Generate BCBS 239 Self-Assessment Report')
    parser.add_argument('--pdf', action='store_true',
                        help='Compile to PDF via pdflatex')
    args = parser.parse_args()

    os.makedirs(_output_dir, exist_ok=True)
    tex_path = os.path.join(_output_dir, 'bcbs239_self_assessment.tex')

    data = load_assessment()
    content = generate_document(data)
    with open(tex_path, 'w') as f:
        f.write(content)
    print(f'LaTeX written: {tex_path}')

    if args.pdf:
        compile_pdf(_output_dir, 'bcbs239_self_assessment.tex')


if __name__ == '__main__':
    main()
