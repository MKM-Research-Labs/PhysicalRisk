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

"""Shared pdflatex compilation for test results."""

import os
import subprocess

from .latex import tex_escape
from .models import MODEL_INFO


def compile_model_pdf(model_id, run_timestamp, history=None):
    """Wrap a per-model fragment in a standalone doc and compile to PDF."""
    info = MODEL_INFO.get(model_id)
    if not info or not info['dir']:
        return None

    from config import config
    script_dir = config.get_project_root() / 'docs' / 'models'
    model_dir = os.path.join(script_dir, info['dir'])
    fragment_path = os.path.join(model_dir, 'test_results.tex')
    if not os.path.isfile(fragment_path):
        return None

    wrapper_path = os.path.join(model_dir, 'test_results_standalone.tex')
    wrapper = [
        r'\documentclass[11pt,a4paper]{article}',
        f'\\newcommand{{\\doctitle}}{{{tex_escape(info["name"])} --- Test Results}}',
        r'\newcommand{\docsubtitle}{Automated Test Documentation for Model Governance}',
        r'\newcommand{\docversion}{1.0}',
        f'\\newcommand{{\\docdate}}{{{run_timestamp.strftime("%d-%B-%Y")}}}',
        r'\newcommand{\docauthor}{David K Kelly}',
        r'\input{../shared/mkm_header}',
        '',
        r'\begin{document}',
        r'\mkmtitlepage',
        r'\mkmlegalpage',
        '',
        f'\\section{{Test Results --- {tex_escape(info["name"])} ({tex_escape(model_id)})}}',
        '',
        f'Tests run on \\textbf{{{run_timestamp.strftime("%d %B %Y at %H:%M:%S")}}}.',
        '',
        r'\input{test_results}',
        '',
        r'\end{document}',
    ]

    with open(wrapper_path, 'w') as f:
        f.write('\n'.join(wrapper))

    try:
        for _ in range(2):
            subprocess.run(
                ['pdflatex', '-interaction=nonstopmode',
                 '-output-directory', model_dir, wrapper_path],
                capture_output=True, cwd=model_dir,
                timeout=30,
            )
        pdf_path = wrapper_path.replace('.tex', '.pdf')
        if os.path.exists(pdf_path):
            final_path = os.path.join(model_dir, 'test_results.pdf')
            os.replace(pdf_path, final_path)
            for ext in ('.aux', '.log', '.out', '.toc'):
                aux = wrapper_path.replace('.tex', ext)
                if os.path.exists(aux):
                    os.remove(aux)
            os.remove(wrapper_path)
            return final_path
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None
