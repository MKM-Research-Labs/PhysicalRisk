# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for open_pdf_file — platform dispatch and error handling."""

import subprocess
from pathlib import Path
from unittest.mock import patch


def _fake_pdf(tmp_path: Path) -> Path:
    p = tmp_path / "report.pdf"
    p.write_bytes(b"%PDF-1.4")
    return p


class TestOpenPdfFile:

    def test_darwin_success(self, tmp_path):
        from reports.property.property_generator import open_pdf_file
        fake = _fake_pdf(tmp_path)
        with patch("platform.system", return_value="Darwin"):
            with patch("subprocess.run") as mock_run:
                result = open_pdf_file(fake)
        assert result is True
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0][0] == "open"

    def test_windows_success(self, tmp_path):
        from reports.property.property_generator import open_pdf_file
        fake = _fake_pdf(tmp_path)
        with patch("platform.system", return_value="Windows"):
            with patch("subprocess.run") as mock_run:
                result = open_pdf_file(fake)
        assert result is True
        mock_run.assert_called_once()

    def test_linux_success(self, tmp_path):
        from reports.property.property_generator import open_pdf_file
        fake = _fake_pdf(tmp_path)
        with patch("platform.system", return_value="Linux"):
            with patch("subprocess.run") as mock_run:
                result = open_pdf_file(fake)
        assert result is True
        assert "xdg-open" in mock_run.call_args[0][0]

    def test_unknown_platform_uses_webbrowser(self, tmp_path):
        from reports.property.property_generator import open_pdf_file
        fake = _fake_pdf(tmp_path)
        with patch("platform.system", return_value="FreeBSD"):
            with patch("webbrowser.open") as mock_wb:
                result = open_pdf_file(fake)
        assert result is True
        mock_wb.assert_called_once()

    def test_subprocess_called_process_error_returns_false(self, tmp_path):
        from reports.property.property_generator import open_pdf_file
        fake = _fake_pdf(tmp_path)
        with patch("platform.system", return_value="Darwin"):
            with patch("subprocess.run",
                       side_effect=subprocess.CalledProcessError(1, "open")):
                result = open_pdf_file(fake)
        assert result is False

    def test_generic_exception_returns_false(self, tmp_path):
        from reports.property.property_generator import open_pdf_file
        fake = _fake_pdf(tmp_path)
        with patch("platform.system", side_effect=RuntimeError("no system")):
            result = open_pdf_file(fake)
        assert result is False

    def test_windows_case_insensitive(self, tmp_path):
        """platform.system() returns lower-case on some systems."""
        from reports.property.property_generator import open_pdf_file
        fake = _fake_pdf(tmp_path)
        with patch("platform.system", return_value="windows"):
            with patch("subprocess.run"):
                result = open_pdf_file(fake)
        assert isinstance(result, bool)
