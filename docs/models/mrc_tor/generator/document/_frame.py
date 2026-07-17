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

"""Static LaTeX preamble and closing frame for the MRC ToR document."""

HEADER = r"""\documentclass[11pt]{article}

\newcommand{\doctitle}{Model Risk Committee}
\newcommand{\docsubtitle}{Terms of Reference}
\newcommand{\docversion}{1.0}
\newcommand{\docdate}{"""

FOOTER = r"""

% ================================================================
\section{Approval}
% ================================================================

\vspace{1cm}
\begin{longtable}{p{6cm}p{7.5cm}}
\textbf{Approved by:} & \\[1.5cm]
\dotfill & \dotfill \\
Johnny Mattimore & David K Kelly \\
Chair, Model Risk Committee & Model Owner, Chief Science Officer \\[1cm]
\textbf{Date:} & \docdate \\
\end{longtable}

% ================================================================
\mkmhistorypage{
\docdate & 1.0 & Initial Terms of Reference & David K Kelly \\
}

\end{document}
"""
