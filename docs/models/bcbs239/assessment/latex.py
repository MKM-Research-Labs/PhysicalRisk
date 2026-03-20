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

"""BCBS 239 assessment LaTeX document generation."""

from datetime import datetime

from .data import score_label, score_color


def tex_escape(text):
    """Escape special LaTeX characters."""
    if not text:
        return ''
    text = str(text)
    text = text.replace('\\', r'\textbackslash{}')
    for old, new in [
        ('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'),
        ('_', r'\_'), ('{', r'\{'), ('}', r'\}'),
        ('~', r'\textasciitilde{}'), ('^', r'\^{}'),
    ]:
        text = text.replace(old, new)
    return text


def generate_document(data):
    """Generate the BCBS 239 self-assessment LaTeX document."""
    today = datetime.now().strftime('%d-%B-%Y')
    principles = data.get('principles', [])

    total_score = sum(p['score'] for p in principles)
    total_max = sum(p['max_score'] for p in principles)
    pct = round(total_score / total_max * 100) if total_max > 0 else 0

    categories = [
        ('Governance and Infrastructure', [1, 2]),
        ('Risk Data Aggregation', [3, 4, 5, 6]),
        ('Risk Reporting Practices', [7, 8, 9, 10, 11]),
        ('Supervisory Review', [12, 13, 14]),
    ]

    doc = r"""\documentclass[11pt]{article}

\newcommand{\doctitle}{BCBS 239 Self-Assessment}
\newcommand{\docsubtitle}{Risk Data Aggregation and Reporting Compliance}
\newcommand{\docversion}{""" + tex_escape(data.get('version', '1.0')) + r"""}
\newcommand{\docdate}{""" + today + r"""}
\newcommand{\docauthor}{""" + tex_escape(data.get('assessor', 'David K Kelly')) + r"""}

\input{../shared/mkm_header}

\begin{document}
\mkmtitlepage
\mkmlegalpage
\tableofcontents
\clearpage

% ================================================================
\section{Executive Summary}
% ================================================================

This document presents the self-assessment of MKM Research Labs against the
14 principles of BCBS~239 (\textit{Principles for effective risk data aggregation
and risk reporting}, Basel Committee on Banking Supervision, January 2013).

The assessment was conducted on \textbf{""" + tex_escape(data.get('assessment_date', today)) + r"""} by
\textbf{""" + tex_escape(data.get('assessor', '')) + r"""}.

\subsection{Overall Compliance Score}

\begin{table}[H]
    \centering
    \caption{Overall Assessment Summary}
    \begin{tabular}{lr}
        \toprule
        Total Score & """ + str(total_score) + r""" / """ + str(total_max) + r""" \\
        Compliance Percentage & \textbf{""" + str(pct) + r"""\%} \\
        Principles Assessed & """ + str(len(principles)) + r""" \\
        Assessment Date & """ + tex_escape(data.get('assessment_date', '')) + r""" \\
        \bottomrule
    \end{tabular}
\end{table}

\subsection{Score by Category}

\begin{table}[H]
    \centering
    \caption{Compliance by BCBS 239 Category}
    \label{tab:category_scores}
    \begin{tabular}{lcccc}
        \toprule
        \textbf{Category} & \textbf{Principles} & \textbf{Score} & \textbf{Max} & \textbf{\%} \\
        \midrule
"""

    for cat_name, cat_ids in categories:
        cat_principles = [p for p in principles if p['id'] in cat_ids]
        cat_score = sum(p['score'] for p in cat_principles)
        cat_max = sum(p['max_score'] for p in cat_principles)
        cat_pct = round(cat_score / cat_max * 100) if cat_max > 0 else 0
        id_range = f'P{cat_ids[0]}--P{cat_ids[-1]}'
        doc += f'        {tex_escape(cat_name)} & {id_range} & {cat_score} & {cat_max} & {cat_pct}\\% \\\\\n'

    doc += r"""        \midrule
        \textbf{Total} & P1--P14 & \textbf{""" + str(total_score) + r"""} & """ + str(total_max) + r""" & \textbf{""" + str(pct) + r"""\%} \\
        \bottomrule
    \end{tabular}
\end{table}

\subsection{Score Distribution}

\begin{table}[H]
    \centering
    \caption{Distribution of Scores Across Principles}
    \begin{tabular}{lcc}
        \toprule
        \textbf{Rating} & \textbf{Score} & \textbf{Count} \\
        \midrule
"""

    for s in [4, 3, 2, 1]:
        count = sum(1 for p in principles if p['score'] == s)
        label = score_label(s)
        doc += f'        {score_color(s)}{{{tex_escape(label)}}} & {s} & {count} \\\\\n'

    doc += r"""        \bottomrule
    \end{tabular}
\end{table}

\clearpage

% ================================================================
\section{Assessment Methodology}
% ================================================================

This self-assessment follows the methodology established by the Basel Committee
in its progress reports on adoption of BCBS~239 (2013, 2014). Each of the 14
principles is scored on a four-point scale:

\begin{table}[H]
    \centering
    \begin{tabular}{cl}
        \toprule
        \textbf{Score} & \textbf{Rating} \\
        \midrule
        4 & \textcolor{green!60!black}{Fully Compliant} --- All requirements met \\
        3 & \textcolor{blue}{Largely Compliant} --- Most requirements met, minor gaps \\
        2 & \textcolor{orange}{Materially Non-compliant} --- Significant gaps remain \\
        1 & \textcolor{red}{Non-compliant} --- Requirements not addressed \\
        \bottomrule
    \end{tabular}
\end{table}

The 14 principles are organised into four categories as defined by BCBS~239:

\begin{enumerate}
    \item \textbf{Governance and Infrastructure} (Principles 1--2): Overarching
          governance arrangements and data architecture.
    \item \textbf{Risk Data Aggregation} (Principles 3--6): Capabilities for
          accurate, complete, timely, and adaptable data aggregation.
    \item \textbf{Risk Reporting Practices} (Principles 7--11): Quality,
          comprehensiveness, clarity, frequency, and distribution of reports.
    \item \textbf{Supervisory Review} (Principles 12--14): Supervisory
          expectations for review, remediation, and cross-border cooperation.
\end{enumerate}

\clearpage
"""

    # Per-category sections with principle details
    for cat_name, cat_ids in categories:
        doc += '\n% ================================================================\n'
        doc += f'\\section{{{tex_escape(cat_name)}}}\n'
        doc += '% ================================================================\n\n'

        cat_principles = [p for p in principles if p['id'] in cat_ids]
        for p in cat_principles:
            pid = p['id']
            title = tex_escape(p['title'])
            sc = p['score']
            status = tex_escape(score_label(sc))

            doc += f'\\subsection{{Principle {pid}: {title}}}\n\n'

            # Score box
            doc += r'\begin{table}[H]' + '\n'
            doc += r'    \centering' + '\n'
            doc += r'    \begin{tabular}{ll}' + '\n'
            doc += r'        \toprule' + '\n'
            doc += f'        Score & {score_color(sc)}{{\\textbf{{{sc}/4 --- {status}}}}} \\\\\n'
            if p.get('target_date'):
                doc += f"        Target Date & {tex_escape(p['target_date'])} \\\\\n"
            doc += r'        \bottomrule' + '\n'
            doc += r'    \end{tabular}' + '\n'
            doc += r'\end{table}' + '\n\n'

            # Description
            doc += r'\paragraph{Principle Description}' + '\n'
            doc += tex_escape(p.get('description', '')) + '\n\n'

            # Evidence
            if p.get('evidence'):
                doc += r'\paragraph{Evidence of Compliance}' + '\n'
                doc += tex_escape(p['evidence']) + '\n\n'

            # Gaps
            if p.get('gaps'):
                doc += r'\paragraph{Identified Gaps}' + '\n'
                doc += tex_escape(p['gaps']) + '\n\n'

            # Remediation
            if p.get('remediation'):
                doc += r'\paragraph{Remediation Plan}' + '\n'
                doc += tex_escape(p['remediation'])
                if p.get('target_date'):
                    doc += f" (Target: {tex_escape(p['target_date'])})"
                doc += '\n\n'

        doc += r'\clearpage' + '\n'

    # Remediation roadmap
    doc += r"""
% ================================================================
\section{Remediation Roadmap}
% ================================================================

The following table summarises all identified gaps and their remediation plans,
ordered by target date.

\begin{longtable}{p{0.5cm}p{3cm}p{5.5cm}p{2.5cm}p{1.5cm}p{2cm}}
    \toprule
    \textbf{\#} & \textbf{Principle} & \textbf{Remediation Action} & \textbf{Gap Summary} & \textbf{Score} & \textbf{Target} \\
    \midrule
    \endhead
"""

    # Sort by target date
    sorted_principles = sorted(principles, key=lambda p: p.get('target_date', '9999'))
    for p in sorted_principles:
        if p.get('remediation'):
            sc = p['score']
            doc += (
                f"    {p['id']} & {tex_escape(p['title'])} & "
                f"{tex_escape(p['remediation'])} & "
                f"{tex_escape((p.get('gaps') or '')[:80])} & "
                f"{score_color(sc)}{{{sc}/4}} & "
                f"{tex_escape(p.get('target_date', ''))} \\\\\n"
            )

    doc += r"""    \bottomrule
\end{longtable}

\clearpage

% ================================================================
\section{Appendix: BCBS 239 Principles}
% ================================================================

For reference, the complete list of the 14 principles as defined by the Basel
Committee on Banking Supervision in January 2013 (\textit{Principles for
effective risk data aggregation and risk reporting}, BCBS 2013).

\begin{longtable}{cp{3cm}p{10.5cm}}
    \toprule
    \textbf{\#} & \textbf{Principle} & \textbf{Description} \\
    \midrule
    \endhead
"""

    for p in principles:
        doc += f"    {p['id']} & {tex_escape(p['title'])} & {tex_escape(p.get('description', ''))} \\\\\n"
        doc += '    \\addlinespace\n'

    doc += r"""    \bottomrule
\end{longtable}

% ================================================================
\mkmhistorypage{
""" + today + r""" & 1.0 & Initial BCBS 239 Self-Assessment & """ + tex_escape(data.get('assessor', 'David K Kelly')) + r""" \\
}

\end{document}
"""
    return doc
