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

"""
Tests for reports.utils.open_pdf — open_pdf_file() platform branches and errors.

Covers: darwin/windows/linux/unknown platform paths, CalledProcessError,
and general Exception fallback.
"""

import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestOpenPdfFile:
    """Tests for open_pdf_file() on different platforms."""

    def _fake_path(self, tmp_path) -> Path:
        p = tmp_path / "report.pdf"
        p.write_bytes(b"%PDF-1.4 fake")
        return p

    def test_darwin_calls_open(self, tmp_path):
        """macOS: subprocess.run(['open', ...]) is called."""
        from reports.utils.open_pdf import open_pdf_file
        p = self._fake_path(tmp_path)
        with patch("reports.utils.open_pdf.platform.system", return_value="Darwin"), \
             patch("reports.utils.open_pdf.subprocess.run") as mock_run:
            result = open_pdf_file(p)
            assert result is True
            assert mock_run.call_args[0][0][0] == "open"

    def test_windows_calls_start(self, tmp_path):
        """Windows: subprocess.run(['start', ...]) is called."""
        from reports.utils.open_pdf import open_pdf_file
        p = self._fake_path(tmp_path)
        with patch("reports.utils.open_pdf.platform.system", return_value="Windows"), \
             patch("reports.utils.open_pdf.subprocess.run") as mock_run:
            result = open_pdf_file(p)
            assert result is True
            assert mock_run.call_args[0][0][0] == "start"

    def test_linux_calls_xdg_open(self, tmp_path):
        """Linux: subprocess.run(['xdg-open', ...]) is called."""
        from reports.utils.open_pdf import open_pdf_file
        p = self._fake_path(tmp_path)
        with patch("reports.utils.open_pdf.platform.system", return_value="Linux"), \
             patch("reports.utils.open_pdf.subprocess.run") as mock_run:
            result = open_pdf_file(p)
            assert result is True
            assert mock_run.call_args[0][0][0] == "xdg-open"

    def test_unknown_platform_uses_webbrowser(self, tmp_path):
        """Unknown platform: falls back to webbrowser.open()."""
        from reports.utils.open_pdf import open_pdf_file
        p = self._fake_path(tmp_path)
        with patch("reports.utils.open_pdf.platform.system", return_value="FreeBSD"), \
             patch("reports.utils.open_pdf.webbrowser.open") as mock_wb:
            result = open_pdf_file(p)
            assert result is True
            mock_wb.assert_called_once()

    def test_called_process_error_returns_false(self, tmp_path):
        """CalledProcessError → returns False."""
        from reports.utils.open_pdf import open_pdf_file
        p = self._fake_path(tmp_path)
        with patch("reports.utils.open_pdf.platform.system", return_value="Darwin"), \
             patch("reports.utils.open_pdf.subprocess.run",
                   side_effect=subprocess.CalledProcessError(1, "open")):
            result = open_pdf_file(p)
            assert result is False

    def test_generic_exception_returns_false(self, tmp_path):
        """Any other exception → returns False."""
        from reports.utils.open_pdf import open_pdf_file
        p = self._fake_path(tmp_path)
        with patch("reports.utils.open_pdf.platform.system",
                   side_effect=RuntimeError("unexpected")):
            result = open_pdf_file(p)
            assert result is False
