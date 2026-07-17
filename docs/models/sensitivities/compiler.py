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

"""Shared pdflatex compilation wrapper for sensitivity analysis."""

import os
import subprocess


def compile_pdf(output_dir, tex_path):
    """Compile a LaTeX file to PDF via pdflatex (two passes for TOC)."""
    try:
        for _ in range(2):
            subprocess.run(
                ['pdflatex', '-interaction=nonstopmode',
                 '-output-directory', output_dir, tex_path],
                capture_output=True, text=True, cwd=output_dir,
                timeout=60,
            )
        pdf_path = tex_path.replace('.tex', '.pdf')
        if os.path.exists(pdf_path):
            size_kb = os.path.getsize(pdf_path) / 1024
            print(f'  PDF generated: {pdf_path} ({size_kb:.1f} KB)')
            return pdf_path
        else:
            print('  PDF compilation failed.')
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print('  pdflatex not available or timed out.')
    return None
