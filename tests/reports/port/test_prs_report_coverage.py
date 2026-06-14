# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only.

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
