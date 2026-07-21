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

"""LaTeX helpers for test results documentation."""


def tex_escape(text):
    """Escape special LaTeX characters."""
    text = text.replace('\\', r'\textbackslash{}')
    for old, new in [
        ('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'),
        ('_', r'\_'), ('{', r'\{'), ('}', r'\}'),
        ('~', r'\textasciitilde{}'), ('^', r'\^{}'),
    ]:
        text = text.replace(old, new)
    return text


def result_colour(outcome):
    """Return LaTeX colour command for outcome."""
    if outcome == 'passed':
        return r'\textcolor{green!60!black}{Pass}'
    elif outcome == 'failed':
        return r'\textcolor{red}{\textbf{FAIL}}'
    elif outcome == 'skipped':
        return r'\textcolor{orange}{Skip}'
    return outcome


def generate_summary_table(model_id, model_name, results):
    """Generate a summary table for one model."""
    total = len(results)
    passed = sum(1 for r in results if r['outcome'] == 'passed')
    failed = sum(1 for r in results if r['outcome'] == 'failed')
    skipped = sum(1 for r in results if r['outcome'] == 'skipped')
    duration = sum(r['duration'] for r in results)

    lines = [
        r'\begin{table}[H]',
        r'    \centering',
        f'    \\caption{{Test Results Summary --- {tex_escape(model_name)} ({tex_escape(model_id)})}}',
        f'    \\label{{tab:test_summary_{model_id.lower().replace("-", "_")}}}',
        r'    \begin{tabular}{lr}',
        r'        \toprule',
        f'        Total Tests & {total} \\\\',
        f'        \\textcolor{{green!60!black}}{{Passed}} & {passed} \\\\',
        f'        \\textcolor{{red}}{{Failed}} & {failed} \\\\',
        f'        Skipped & {skipped} \\\\',
        f'        Duration & {duration:.2f}s \\\\',
        r'        \bottomrule',
        r'    \end{tabular}',
        r'\end{table}',
    ]
    return '\n'.join(lines)


def generate_detail_table(model_id, model_name, results, criteria_cache=None):
    """Generate detailed test results table for one model."""
    label = model_id.lower().replace('-', '_')
    criteria_cache = criteria_cache or {}

    lines = [
        r'\begin{longtable}{p{6cm}p{5.5cm}cc}',
        # The \label must sit inside the caption row, before the \\ that ends
        # it. Emitting it after the row break starts a fresh longtable row, so
        # the following \toprule lands mid-row and pdflatex raises
        # "Misplaced \noalign".
        f'    \\caption{{Detailed Test Results --- {tex_escape(model_name)}}}'
        f'\\label{{tab:test_detail_{label}}} \\\\',
        r'    \toprule',
        r'    \textbf{Test Description} & \textbf{Acceptance Criteria} & \textbf{Result} & \textbf{Time} \\',
        r'    \midrule',
        r'    \endfirsthead',
        r'    \toprule',
        r'    \textbf{Test Description} & \textbf{Acceptance Criteria} & \textbf{Result} & \textbf{Time} \\',
        r'    \midrule',
        r'    \endhead',
        r'    \bottomrule',
        r'    \endfoot',
    ]

    for r in sorted(results, key=lambda x: (x['class'], x['name'])):
        desc = r.get('description', '')
        if not desc:
            desc = r['name'].replace('_', ' ').replace('test ', '').capitalize()

        params = r.get('params', '')
        if params:
            desc += f' [{params}]'

        key = (r['file'], r['class'], r['name'])
        assertions = criteria_cache.get(key, [])
        if assertions:
            criteria_parts = []
            for a in assertions[:2]:
                a_short = a if len(a) <= 60 else a[:57] + '...'
                criteria_parts.append(f'\\texttt{{{tex_escape(a_short)}}}')
            criteria = '; '.join(criteria_parts)
            if len(assertions) > 2:
                criteria += f' (+{len(assertions)-2} more)'
        else:
            criteria = '---'

        result_str = result_colour(r['outcome'])
        dur = f"{r['duration']:.3f}s"

        lines.append(
            f'    {tex_escape(desc)} & '
            f'{{\\scriptsize {criteria}}} & '
            f'{result_str} & '
            f'{dur} \\\\'
        )

    lines.append(r'\end{longtable}')
    return '\n'.join(lines)


def generate_failure_section(results):
    """Generate details for failed tests."""
    failed = [r for r in results if r['outcome'] == 'failed']
    if not failed:
        return ''

    lines = [
        '',
        r'\subsubsection*{Failed Test Details}',
        '',
    ]
    for r in failed:
        lines.append(f'\\paragraph{{{tex_escape(r["name"])}}}')
        lines.append(f'File: \\texttt{{{tex_escape(r["file"])}}}')
        lines.append('')
        longrepr = r['longrepr']
        if len(longrepr) > 800:
            longrepr = longrepr[:800] + '\n... (truncated)'
        lines.append(r'\begin{lstlisting}[language={},basicstyle=\ttfamily\scriptsize,breaklines=true]')
        lines.append(longrepr)
        lines.append(r'\end{lstlisting}')
        lines.append('')

    return '\n'.join(lines)
