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
