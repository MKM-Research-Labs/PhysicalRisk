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

"""Gate test for the styling audit (§4.8, coding rule R7).

Zero tolerance on two things, for different reasons.

A **colour literal** in a gated surface is a second place the platform's appearance is
decided. It is visible in a diff, so this gate is really about stopping the backlog
growing back once a surface has been converted.

An **undefined token** is the one that has to be gated everywhere, JavaScript included.
``var(--acccent)`` is not an error in CSS — the browser drops the declaration and the
element inherits, so the control renders in a plausible colour and nothing complains.
It reaches a screen invisibly, on whichever panel nobody opened, and the only place it
can be caught is here.

The JavaScript colour backlog is deliberately *not* gated: step 6 of
docs/refactor/theme_centralisation_plan.md is still converting it. It is asserted to be
shrinking rather than absent, so the remaining work stays visible instead of exempt.
"""

import pytest

from docs.models.full_audit.sections_tests.styling import (
    GATED_SUFFIXES, REPORTED_SUFFIXES, scan_repo, scan_text,
)


@pytest.fixture(scope="module")
def scan():
    return scan_repo()


class TestGatedSurfaces:
    def test_no_colour_literals_outside_config_theme(self, scan):
        findings = scan["gated"]
        detail = ", ".join(f'{f["path"]}:{f["line"]} {f["snippet"]}' for f in findings[:20])
        assert findings == [], f"colour literals in gated assets: {detail}"

    def test_every_token_reference_resolves(self, scan):
        """A var() naming nothing renders as an inherited colour, silently."""
        findings = scan["undefined"]
        detail = ", ".join(f'{f["path"]}:{f["line"]} {f["snippet"]}' for f in findings[:20])
        assert findings == [], f"undefined design tokens: {detail}"

    def test_css_and_html_are_the_gated_surfaces(self):
        """Widening the gate is a deliberate act, not a side effect of a rename."""
        assert set(GATED_SUFFIXES) == {".css", ".html"}

    def test_the_scan_actually_reached_the_assets(self, scan):
        """A scan that found nothing to look at would pass every assertion above."""
        assert scan["scanned"] > 100
        assert scan["tokens"] > 200


class TestReportedBacklog:
    def test_javascript_is_reported_not_gated(self):
        assert REPORTED_SUFFIXES == (".js",)

    def test_backlog_is_not_growing(self, scan):
        """A ceiling, lowered as step 6 converts each batch.

        Not an exact figure: that would fail on every commit that converts a file,
        which trains people to edit the number rather than read it. A ceiling only
        fails when the backlog *grows*, which is the thing worth blocking.
        """
        assert scan["backlog"], "the backlog is empty — gate .js and delete this test"
        assert len(scan["backlog"]) <= 3200, (
            f'JavaScript colour backlog grew to {len(scan["backlog"])}; it should only '
            f'shrink as step 6 converts each batch'
        )


class TestScanner:
    """The scanner's own false-positive guards, each learned from a real one."""

    def test_html_numeric_entities_are_not_colours(self):
        """``&#128196;`` is a document icon. Six of them sat in mg-audit-reports.js."""
        found = scan_text("var icons = {PDF: '&#128196;'};", "x.js", ".js")
        assert found["literals"] == []

    def test_id_selectors_are_not_colours(self):
        found = scan_text("#abc-panel { display: none; }", "x.css", ".css")
        assert found["literals"] == []

    def test_a_real_literal_is_found(self):
        found = scan_text("a { color: #1976d2; }", "x.css", ".css")
        assert [f["snippet"] for f in found["literals"]] == ["#1976d2"]

    def test_rgba_is_a_literal(self):
        found = scan_text("a { background: rgba(0,0,0,0.4); }", "x.css", ".css")
        assert len(found["literals"]) == 1

    def test_colours_named_in_comments_are_not_findings(self):
        """Explaining why colours are not written down must not be a finding."""
        assert scan_text("/* was #1976d2 */\na { color: var(--accent); }",
                         "x.css", ".css")["literals"] == []
        assert scan_text("// was #1976d2\nvar a = Theme.value('accent');",
                         "x.js", ".js")["literals"] == []

    def test_a_url_is_not_a_comment(self):
        """The // comment strip must not eat the rest of a line after https://."""
        found = scan_text("var u = 'https://x.example/#1976d2';", "x.js", ".js")
        assert len(found["literals"]) == 1

    def test_undefined_token_is_reported(self):
        found = scan_text("a { color: var(--no-such-token); }", "x.css", ".css")
        assert [f["snippet"] for f in found["undefined"]] == ["--no-such-token"]

    def test_defined_token_is_not_reported(self):
        found = scan_text("a { color: var(--accent); }", "x.css", ".css")
        assert found["undefined"] == []

    def test_line_numbers_survive_comment_stripping(self):
        """A finding has to point at the line a person would open."""
        text = "/* a\n   multi-line\n   comment */\na { color: #1976d2; }"
        found = scan_text(text, "x.css", ".css")
        assert found["literals"][0]["line"] == 4
