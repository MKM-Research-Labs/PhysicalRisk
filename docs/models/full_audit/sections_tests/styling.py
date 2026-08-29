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

"""Subsection 4.8: styling governance audit (coding rule R7).

Ported from MKM-ModelRisk's ``audit/styling.py``, where the same check is rule R10.
An audit check, not a model, sitting beside the path-definition (4.3) and
database-usage (4.6) audits. Policy: **every visual parameter must be housed in the**
``config/theme`` **package** — colours, and in time the type, spacing and radius
scales. Modules elsewhere refer to a token, by ``var(--name)`` in CSS and HTML or
``Theme.value('name')`` in JavaScript, rather than writing a value down.

**Two findings, and the second is the one that bites.** A colour literal is visible —
you can read it and see it is wrong. A reference to a token that does not exist is
not: the browser drops the declaration in silence, the element renders with whatever
it inherits, and nobody notices until an adopter's rebrand leaves one control the old
colour, on whichever panel nobody happened to open. Both are checked.

**Gated versus reported.** ``.css`` and ``.html`` are at zero as of step 4 of
docs/refactor/theme_centralisation_plan.md and are gated: a new literal in either
fails the build. ``.js`` is still being converted in step 6, so its literals are
*counted and listed* rather than gated — a backlog that shrinks in the open beats a
silent exemption, and the count is what tells you step 6 is finished. Undefined token
references are gated everywhere, including JavaScript, because that failure is
invisible and has no backlog to work through.

The scan (``scan_repo`` / ``scan_text``) is exercised by the gate test in
``tests/commands/test_styling_report.py``; ``_build_styling`` renders the read-only
compliance section for the consolidated audit report.
"""

import re
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Spacer

from config.theme import THEME
from config.theme.registry import SANCTIONED_PACKAGE

from .._constants import NAVY

# A CSS colour. Two guards, both learned from false positives on real markup: the
# trailing one keeps ``#abc`` in the id selector ``#abc-panel`` out, and the leading
# one keeps numeric character references out — ``&#128196;`` is a document icon, not a
# colour, and its digits are all decimal.
_COLOUR = re.compile(
    r"(?<!&)#[0-9a-fA-F]{3,8}(?![-\w])"
    r"|\b(?:rgba?|hsla?)\s*\("
    # A bare CSS colour keyword in a declaration. ``background:white`` is every bit as
    # much a hardcoded colour as ``background:#ffffff`` and reads as innocent, which is
    # why it survived the first sweep of every surface: 78 of them sat in the
    # governance panels after the hex conversion. Anchored to a property so the English
    # word "white" in a label is not a finding.
    r"|(?:background|background-color|color|border|border-top|border-bottom|border-left"
    r"|border-right|border-color|outline|fill|stroke)\s*:\s*"
    r"(?:white|black|red|blue|green|grey|gray|silver|orange)\b")
_VAR_REFERENCE = re.compile(r"var\(\s*--([a-zA-Z0-9_-]+)")
_CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_JS_LINE_COMMENT = re.compile(r"(?<!:)//.*$", re.MULTILINE)

#: Trees whose assets the console and the tools actually serve.
_ASSET_DIRS = ("src/static", "src/templates", "tools")

#: Suffixes at zero and held there. A literal in one of these fails the build.
GATED_SUFFIXES = (".css", ".html")

#: Suffixes scanned and reported but not yet gated — step 6's remaining work.
REPORTED_SUFFIXES = (".js",)

#: The one place a visual parameter may be written down.
SANCTIONED = SANCTIONED_PACKAGE

#: This module holds colour-shaped text in its own regexes and prose.
_SELF = "docs/models/full_audit"


def _asset_files(root: Path):
    """Every asset the scan covers, gated and reported alike."""
    for directory in _ASSET_DIRS:
        base = root / directory
        if not base.is_dir():
            continue
        for suffix in GATED_SUFFIXES + REPORTED_SUFFIXES:
            for path in sorted(base.rglob(f"*{suffix}")):
                if "node_modules" in path.parts or SANCTIONED in str(path):
                    continue
                yield path


def _blank(match) -> str:
    """The matched text as spaces, with its newlines kept.

    Blanking a multi-line comment with ``" " * len(...)`` eats the newlines inside it,
    so every finding after it reports a line number that is too low — and a finding
    that points at the wrong line is worse than no finding, because it sends the reader
    somewhere innocent. Keeping the newlines keeps the file's line count intact.
    """
    return "".join("\n" if char == "\n" else " " for char in match.group(0))


def _without_comments(text: str, suffix: str) -> str:
    """*text* with comments blanked, keeping every line in place.

    Naming a colour while explaining why colours are not written down here must not
    itself be a finding.
    """
    text = _CSS_COMMENT.sub(_blank, text)
    if suffix == ".js":
        text = _JS_LINE_COMMENT.sub(_blank, text)
    return text


#: A colour built from variables rather than written down — ``'hsl(' + hue + ',' …``.
#: The curve chart spreads hues evenly across however many gauges are on screen, which
#: is generated colour, not a hardcoded one: there is no value here for config to own.
_COMPUTED_COLOUR = re.compile(r"\b(?:rgba?|hsla?)\(\s*'\s*\+|\+\s*'\s*\)")


def scan_text(text: str, path: str, suffix: str) -> dict:
    """The literals and undefined token references in one file's text."""
    literals, undefined = [], []
    clean = _without_comments(text, suffix)
    for number, line in enumerate(clean.splitlines(), start=1):
        if _COMPUTED_COLOUR.search(line):
            continue
        for match in _COLOUR.finditer(line):
            literals.append({"path": path, "line": number,
                             "snippet": match.group(0).rstrip("(").strip()})
    # The same comment-stripped text as the literal scan. theme.js documents its own
    # helpers by naming ``var(--token)`` in prose, and a scan that reads raw text
    # reports that as a reference to a token called "token".
    for number, line in enumerate(clean.splitlines(), start=1):
        for match in _VAR_REFERENCE.finditer(line):
            if match.group(1) not in THEME:
                undefined.append({"path": path, "line": number,
                                  "snippet": "--" + match.group(1)})
    return {"literals": literals, "undefined": undefined}


def scan_repo(root: Path = None) -> dict:
    """Scan the served assets. Gated findings, reported backlog, and token misses."""
    if root is None:
        from config import config
        root = config.get_project_root()
    root = Path(root)

    gated, backlog, undefined, scanned = [], [], [], 0
    for path in _asset_files(root):
        relative = str(path.relative_to(root))
        if relative.startswith(_SELF):
            continue
        scanned += 1
        found = scan_text(path.read_text(encoding="utf-8"), relative, path.suffix)
        if path.suffix in GATED_SUFFIXES:
            gated.extend(found["literals"])
        else:
            backlog.extend(found["literals"])
        undefined.extend(found["undefined"])
    return {
        "scanned": scanned,
        "gated": gated,
        "backlog": backlog,
        "undefined": undefined,
        "tokens": len(THEME),
        "files_with_findings": sorted({f["path"] for f in gated + undefined}),
    }


def _build_styling(styles) -> list:
    """4.8 — report colour literals and undefined token references."""
    elems = [Spacer(1, 5 * mm),
             Paragraph('4.8 Styling Audit', styles['h3']),
             HRFlowable(width='100%', thickness=1, color=NAVY),
             Spacer(1, 2 * mm),
             Paragraph(
                 'Policy: every visual parameter must be housed in the '
                 '<b>config/theme</b> package. Assets refer to a token — '
                 '<b>var(--name)</b> in CSS and HTML, <b>Theme.value(\'name\')</b> in '
                 'JavaScript — rather than writing a colour down. CSS and HTML are a '
                 'zero-tolerance gate (tests/commands/test_styling_report.py); '
                 'JavaScript is reported as a backlog while step 6 of the theme '
                 'migration converts it. A <b>var()</b> naming an undefined token is '
                 'gated everywhere: the browser drops the declaration silently, so '
                 'that failure reaches a screen invisibly.', styles['body']),
             Spacer(1, 2 * mm)]

    try:
        scan = scan_repo()
    except Exception as exc:                                  # pragma: no cover
        elems.append(Paragraph(f'Could not run styling audit: {exc}', styles['body']))
        return elems

    from ..results_json import write_results
    write_results('styling', {
        'files_scanned': scan['scanned'],
        'tokens_defined': scan['tokens'],
        'violations': len(scan['gated']),
        'undefined_tokens': len(scan['undefined']),
        'javascript_backlog': len(scan['backlog']),
    })

    elems.append(Paragraph(
        f'Files scanned: <b>{scan["scanned"]}</b> &nbsp;|&nbsp; '
        f'Tokens defined: <b>{scan["tokens"]}</b> &nbsp;|&nbsp; '
        f'Gated violations: <b>{len(scan["gated"])}</b> &nbsp;|&nbsp; '
        f'Undefined tokens: <b>{len(scan["undefined"])}</b> &nbsp;|&nbsp; '
        f'JavaScript backlog: <b>{len(scan["backlog"])}</b>.', styles['body']))
    elems.append(Spacer(1, 2 * mm))

    if not scan['gated'] and not scan['undefined']:
        elems.append(Paragraph(
            'Every colour in the gated surfaces comes from config/theme, and every '
            'token reference resolves. <b>PASS</b>', styles['body']))
    else:
        for label, findings in (('Colour literals outside config/theme', scan['gated']),
                                ('Undefined design tokens', scan['undefined'])):
            if not findings:
                continue
            elems.append(Paragraph(f'<b>{label}</b>', styles['body']))
            for finding in findings[:40]:
                elems.append(Paragraph(
                    f'{finding["path"]}:{finding["line"]} — {finding["snippet"]}',
                    styles['small']))
            if len(findings) > 40:
                elems.append(Paragraph(
                    f'… and {len(findings) - 40} more.', styles['small']))
            elems.append(Spacer(1, 2 * mm))

    if scan['backlog']:
        elems.append(Paragraph(
            f'<b>JavaScript backlog</b>: {len(scan["backlog"])} colour literals remain '
            f'in <b>.js</b> assets, pending step 6 of the theme migration. Reported '
            f'rather than gated so the remaining work is visible rather than exempt.',
            styles['body']))
    return elems


__all__ = ['scan_repo', 'scan_text', 'GATED_SUFFIXES', 'REPORTED_SUFFIXES',
           '_build_styling']
