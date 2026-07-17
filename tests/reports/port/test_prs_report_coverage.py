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

"""Coverage test for PRSPortfolioReport's default output-path branch — when
no explicit output_path is given it lands under audit/archive/."""

from reports.port.prs_report import PRSPortfolioReport


class TestPRSReportDefaultPath:
    def test_default_output_path_under_audit_archive(self, tmp_path, monkeypatch):
        import config as config_pkg

        out_root = tmp_path / "out"
        monkeypatch.setattr(config_pkg.config, "get_output_dir", lambda: out_root)

        report = PRSPortfolioReport(tmp_path / "input")  # no output_path -> else branch
        expected = out_root / "audit" / "archive" / "prs_portfolio_report.pdf"
        assert report.output_path == expected          # lines 40, 43, 45
        assert report.output_path.parent.exists()       # mkdir ran (line 44)
