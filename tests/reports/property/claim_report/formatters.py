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

"""Tests for formatters, constants, styles and layouts."""

import pytest
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import Paragraph


# ---------------------------------------------------------------------------
# formatters.py
# ---------------------------------------------------------------------------

class TestFmtGbp:
    def test_positive_float(self):
        from reports.property.claim.formatters import fmt_gbp
        assert fmt_gbp(1234.56) == '£1,235'

    def test_zero(self):
        from reports.property.claim.formatters import fmt_gbp
        assert fmt_gbp(0) == '£0'

    def test_large_value(self):
        from reports.property.claim.formatters import fmt_gbp
        result = fmt_gbp(1_000_000)
        assert '1,000,000' in result
        assert result.startswith('£')

    def test_non_numeric_fallback(self):
        from reports.property.claim.formatters import fmt_gbp
        assert fmt_gbp('N/A') == 'N/A'

    def test_none_fallback(self):
        from reports.property.claim.formatters import fmt_gbp
        result = fmt_gbp(None)
        assert result == 'None'

    def test_negative(self):
        from reports.property.claim.formatters import fmt_gbp
        result = fmt_gbp(-5000)
        assert '5,000' in result


class TestSeqTypeColor:
    def test_isolated(self):
        from reports.property.claim.formatters import seq_type_color
        from reportlab.lib import colors
        assert seq_type_color('isolated') == colors.lightblue

    def test_doublet(self):
        from reports.property.claim.formatters import seq_type_color
        from reportlab.lib import colors
        assert seq_type_color('doublet') == colors.lightyellow

    def test_cluster(self):
        from reports.property.claim.formatters import seq_type_color
        from reportlab.lib import colors
        assert seq_type_color('cluster') == colors.lightsalmon

    def test_persistent(self):
        from reports.property.claim.formatters import seq_type_color
        from reportlab.lib import colors
        assert seq_type_color('persistent') == colors.mistyrose

    def test_unknown_returns_white(self):
        from reports.property.claim.formatters import seq_type_color
        from reportlab.lib import colors
        assert seq_type_color('unknown') == colors.white

    def test_none_returns_white(self):
        from reports.property.claim.formatters import seq_type_color
        from reportlab.lib import colors
        assert seq_type_color(None) == colors.white

    def test_case_insensitive(self):
        from reports.property.claim.formatters import seq_type_color
        from reportlab.lib import colors
        assert seq_type_color('DOUBLET') == colors.lightyellow


# ---------------------------------------------------------------------------
# constants.py
# ---------------------------------------------------------------------------

class TestConstants:
    def test_margin_positive(self):
        from reports.property.claim.constants import MARGIN
        assert MARGIN > 0

    def test_page_dimensions(self):
        from reports.property.claim.constants import PAGE_H, PAGE_W
        assert PAGE_W > 0
        assert PAGE_H > 0
        # A4 portrait: width < height
        assert PAGE_W < PAGE_H


# ---------------------------------------------------------------------------
# styles.py
# ---------------------------------------------------------------------------

class TestSetupStyles:
    def test_returns_stylesheet(self, styles):
        from reportlab.lib.styles import StyleSheet1
        assert isinstance(styles, StyleSheet1)

    def test_required_keys(self, styles):
        required = [
            'ClaimTitle', 'ClaimSubTitle', 'ClaimRefBanner',
            'SectionHeader', 'SubSectionHeader', 'BodyText9', 'BodyText10',
            'FooterNote', 'NoteBox', 'StatsBar', 'SignatureLine', 'Disclaimer',
        ]
        for key in required:
            assert key in styles, f'Missing style key: {key}'

    def test_styles_are_paragraph_styles(self, styles):
        from reportlab.lib.styles import ParagraphStyle
        for key in ['ClaimTitle', 'SectionHeader', 'BodyText9', 'Disclaimer']:
            assert isinstance(styles[key], ParagraphStyle), \
                f'{key} is not a ParagraphStyle'


# ---------------------------------------------------------------------------
# layouts.py
# ---------------------------------------------------------------------------

class TestLayouts:
    def test_white_hdr_style_returns_paragraph_style(self, styles):
        from reportlab.lib.styles import ParagraphStyle
        from reports.property.claim.layouts import white_hdr_style
        s = white_hdr_style(styles)
        assert isinstance(s, ParagraphStyle)
        assert s.fontName == 'Helvetica-Bold'

    def test_body_style_default(self, styles):
        from reportlab.lib.styles import ParagraphStyle
        from reports.property.claim.layouts import body_style
        s = body_style(styles)
        assert isinstance(s, ParagraphStyle)
        assert s.fontName == 'Helvetica'

    def test_body_style_bold(self, styles):
        from reports.property.claim.layouts import body_style
        s = body_style(styles, font='Helvetica-Bold')
        assert s.fontName == 'Helvetica-Bold'

    def test_body_style_alignment(self, styles):
        from reports.property.claim.layouts import body_style
        s = body_style(styles, align=TA_CENTER)
        assert s.alignment == TA_CENTER

    def test_build_header_footer_callable(self):
        from reports.property.claim.layouts import build_header_footer
        cb = build_header_footer('CLM-TEST-001')
        assert callable(cb)
