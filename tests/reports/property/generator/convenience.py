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

"""Tests for the generate_property_report convenience function."""

from unittest.mock import patch

from .conftest import minimal_property, minimal_mortgage, mock_generator

_PROP = minimal_property()
_MORT = minimal_mortgage()

_TARGET = "reports.property.property_generator.PropertyReportGenerator"


class TestGeneratePropertyReportConvenienceFunction:

    def test_property_only_type(self, tmp_path):
        mock, _ = mock_generator(tmp_path)
        with patch(_TARGET, return_value=mock):
            from reports.property.property_generator import generate_property_report
            generate_property_report(_PROP, output_dir=tmp_path,
                                     report_type="property-only", auto_open=False)
        mock.generate_property_only_report.assert_called_once()

    def test_mortgage_focused_type_with_mortgage(self, tmp_path):
        mock, _ = mock_generator(tmp_path)
        with patch(_TARGET, return_value=mock):
            from reports.property.property_generator import generate_property_report
            generate_property_report(_PROP, rloan_data=_MORT,
                                     output_dir=tmp_path, report_type="mortgage-focused",
                                     auto_open=False)
        mock.generate_mortgage_focused_report.assert_called_once()

    def test_mortgage_focused_without_mortgage_falls_back(self, tmp_path):
        """mortgage-focused with no rloan_data falls back to generate_report."""
        mock, _ = mock_generator(tmp_path)
        with patch(_TARGET, return_value=mock):
            from reports.property.property_generator import generate_property_report
            generate_property_report(_PROP, rloan_data=None,
                                     output_dir=tmp_path, report_type="mortgage-focused",
                                     auto_open=False)
        mock.generate_report.assert_called_once()

    def test_risk_focused_type(self, tmp_path):
        mock, _ = mock_generator(tmp_path)
        with patch(_TARGET, return_value=mock):
            from reports.property.property_generator import generate_property_report
            generate_property_report(_PROP, output_dir=tmp_path,
                                     report_type="risk-focused", auto_open=False)
        mock.generate_risk_focused_report.assert_called_once()

    def test_full_type_falls_back_to_generate_report(self, tmp_path):
        mock, _ = mock_generator(tmp_path)
        with patch(_TARGET, return_value=mock):
            from reports.property.property_generator import generate_property_report
            generate_property_report(_PROP, output_dir=tmp_path,
                                     report_type="full", auto_open=False)
        mock.generate_report.assert_called_once()

    def test_unknown_type_falls_back_to_generate_report(self, tmp_path):
        mock, _ = mock_generator(tmp_path)
        with patch(_TARGET, return_value=mock):
            from reports.property.property_generator import generate_property_report
            generate_property_report(_PROP, output_dir=tmp_path,
                                     report_type="unknown_xyz", auto_open=False)
        mock.generate_report.assert_called_once()

    def test_returns_path(self, tmp_path):
        mock, fake_pdf = mock_generator(tmp_path)
        with patch(_TARGET, return_value=mock):
            from reports.property.property_generator import generate_property_report
            result = generate_property_report(_PROP, output_dir=tmp_path,
                                              report_type="full", auto_open=False)
        assert result == fake_pdf

    def test_auto_open_false_skips_open(self, tmp_path):
        mock, _ = mock_generator(tmp_path)
        with patch(_TARGET, return_value=mock):
            with patch("reports.property.property_generator.open_pdf_file") as mock_open:
                from reports.property.property_generator import generate_property_report
                generate_property_report(_PROP, output_dir=tmp_path,
                                         report_type="full", auto_open=False)
        mock_open.assert_not_called()

    def test_auto_open_true_calls_open(self, tmp_path):
        mock, _ = mock_generator(tmp_path)
        with patch(_TARGET, return_value=mock):
            with patch("reports.property.property_generator.open_pdf_file",
                       return_value=True) as mock_open:
                from reports.property.property_generator import generate_property_report
                generate_property_report(_PROP, output_dir=tmp_path,
                                         report_type="full", auto_open=True)
        mock_open.assert_called_once()

    def test_auto_open_exception_does_not_raise(self, tmp_path):
        mock, _ = mock_generator(tmp_path)
        with patch(_TARGET, return_value=mock):
            with patch("reports.property.property_generator.open_pdf_file",
                       side_effect=OSError("no viewer")):
                from reports.property.property_generator import generate_property_report
                result = generate_property_report(_PROP, output_dir=tmp_path,
                                                  report_type="full", auto_open=True)
        assert result is not None
