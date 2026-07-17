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

"""BCBS 239 assessment data loading and score utilities."""

import json
import os

from config import config

# Governance metadata is version-controlled repo content under
# docs/models/governance_data/, not shared data/.
_data_path = os.path.join(
    str(config.get_governance_data_dir()), 'bcbs239_assessment.json')


def load_assessment():
    """Load assessment data from JSON."""
    with open(_data_path, 'r') as f:
        return json.load(f)


def score_label(score):
    """Return human-readable label for a score."""
    return {
        1: 'Non-compliant',
        2: 'Materially Non-compliant',
        3: 'Largely Compliant',
        4: 'Fully Compliant',
    }.get(score, 'Unknown')


def score_color(score):
    """Return LaTeX colour command for a score."""
    return {
        1: r'\textcolor{red}',
        2: r'\textcolor{orange}',
        3: r'\textcolor{blue}',
        4: r'\textcolor{green!60!black}',
    }.get(score, '')
