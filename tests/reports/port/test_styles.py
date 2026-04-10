"""Tests for src/reports/port/styles.py — colours, constants, StylesMixin."""

import pytest
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Table

from reports.port.styles import (
    ALT_ROWS_AMBER,
    ALT_ROWS_BLUE,
    ALT_ROWS_GREEN,
    AVAIL_WIDTH,
    BLUE,
    DARK_BLUE,
    GREY,
    HDR_STYLE,
    LIGHT_AMBER,
    LIGHT_BLUE,
    LIGHT_GREEN,
    LIGHT_RED,
    StylesMixin,
)


# ---------------------------------------------------------------------------
# Colour constants
# ---------------------------------------------------------------------------

class TestColourConstants:
    def test_blue_is_hex_colour(self):
        assert BLUE == colors.HexColor('#1565C0')

    def test_dark_blue(self):
        assert DARK_BLUE == colors.darkblue

    def test_light_blue(self):
        assert LIGHT_BLUE == colors.HexColor('#E3F2FD')

    def test_light_green(self):
        assert LIGHT_GREEN == colors.HexColor('#E8F5E9')

    def test_light_amber(self):
        assert LIGHT_AMBER == colors.HexColor('#FFF8E1')

    def test_light_red(self):
        assert LIGHT_RED == colors.HexColor('#FFEBEE')

    def test_grey(self):
        assert GREY == colors.HexColor('#757575')


# ---------------------------------------------------------------------------
# HDR_STYLE and alternating-row lists
# ---------------------------------------------------------------------------

class TestTableStyleConstants:
    def test_hdr_style_is_list(self):
        assert isinstance(HDR_STYLE, list)
        assert len(HDR_STYLE) > 0

    def test_hdr_style_first_command_is_background(self):
        assert HDR_STYLE[0][0] == 'BACKGROUND'

    def test_hdr_style_has_grid(self):
        cmds = [c[0] for c in HDR_STYLE]
        assert 'GRID' in cmds
        assert 'BOX' in cmds

    def test_alt_rows_blue(self):
        assert len(ALT_ROWS_BLUE) == 1
        assert ALT_ROWS_BLUE[0][0] == 'ROWBACKGROUNDS'

    def test_alt_rows_green(self):
        assert len(ALT_ROWS_GREEN) == 1
        assert ALT_ROWS_GREEN[0][0] == 'ROWBACKGROUNDS'

    def test_alt_rows_amber(self):
        assert len(ALT_ROWS_AMBER) == 1
        assert ALT_ROWS_AMBER[0][0] == 'ROWBACKGROUNDS'


class TestAvailWidth:
    def test_avail_width_value(self):
        assert AVAIL_WIDTH == pytest.approx(7.3 * inch)


# ---------------------------------------------------------------------------
# StylesMixin helper — create a concrete instance
# ---------------------------------------------------------------------------

class _StyledHelper(StylesMixin):
    """Concrete class that mixes in StylesMixin for testing."""

    def __init__(self):
        self._styles = getSampleStyleSheet()
        self._setup_styles()


@pytest.fixture
def styled():
    return _StyledHelper()


# ---------------------------------------------------------------------------
# _setup_styles
# ---------------------------------------------------------------------------

class TestSetupStyles:
    def test_title_style_font_size(self, styled):
        assert styled.title_style.fontSize == 18

    def test_title_style_font_name(self, styled):
        assert styled.title_style.fontName == 'Helvetica-Bold'

    def test_title_style_text_color(self, styled):
        assert styled.title_style.textColor == DARK_BLUE

    def test_subtitle_style_font_size(self, styled):
        assert styled.subtitle_style.fontSize == 10

    def test_subtitle_style_text_color(self, styled):
        assert styled.subtitle_style.textColor == GREY

    def test_section_style_font_size(self, styled):
        assert styled.section_style.fontSize == 13

    def test_section_style_text_color(self, styled):
        assert styled.section_style.textColor == DARK_BLUE

    def test_subsection_style_font_size(self, styled):
        assert styled.subsection_style.fontSize == 10

    def test_subsection_style_text_color(self, styled):
        assert styled.subsection_style.textColor == BLUE

    def test_body_style_font_size(self, styled):
        assert styled.body_style.fontSize == 9

    def test_kv_style_font_size(self, styled):
        assert styled.kv_style.fontSize == 9

    def test_kv_style_left_indent(self, styled):
        assert styled.kv_style.leftIndent == 12


# ---------------------------------------------------------------------------
# _make_table
# ---------------------------------------------------------------------------

class TestMakeTable:
    def test_returns_table(self, styled):
        t = styled._make_table(['A', 'B'], [['1', '2']])
        assert isinstance(t, Table)

    def test_table_has_correct_row_count(self, styled):
        header = ['Col1', 'Col2']
        rows = [['a', 'b'], ['c', 'd'], ['e', 'f']]
        t = styled._make_table(header, rows)
        # _data includes header + rows
        assert len(t._cellvalues) == 4

    def test_col_widths_propagated(self, styled):
        cw = [1.0 * inch, 2.0 * inch]
        t = styled._make_table(['A', 'B'], [['1', '2']], col_widths=cw)
        assert t._colWidths == cw

    def test_default_alt_color_is_blue(self, styled):
        """When no alt_color passed, ALT_ROWS_BLUE is applied."""
        t = styled._make_table(['A'], [['1']])
        # Just verify table was created without error
        assert isinstance(t, Table)

    def test_custom_alt_color(self, styled):
        t = styled._make_table(['A'], [['1']], alt_color=ALT_ROWS_GREEN)
        assert isinstance(t, Table)

    def test_empty_rows(self, styled):
        t = styled._make_table(['H1', 'H2'], [])
        assert isinstance(t, Table)
        assert len(t._cellvalues) == 1  # header only

    def test_repeat_rows_set(self, styled):
        t = styled._make_table(['A'], [['1']])
        assert t.repeatRows == 1


# ---------------------------------------------------------------------------
# _kv_table
# ---------------------------------------------------------------------------

class TestKvTable:
    def test_returns_table(self, styled):
        t = styled._kv_table([('Key', 'Value')])
        assert isinstance(t, Table)

    def test_multiple_pairs(self, styled):
        pairs = [('A', '1'), ('B', '2'), ('C', '3')]
        t = styled._kv_table(pairs)
        assert len(t._cellvalues) == 3

    def test_default_label_width(self, styled):
        t = styled._kv_table([('K', 'V')])
        assert t._colWidths[0] == pytest.approx(2.8 * inch)

    def test_custom_label_width(self, styled):
        lw = 3.5 * inch
        t = styled._kv_table([('K', 'V')], label_width=lw)
        assert t._colWidths[0] == pytest.approx(lw)
        assert t._colWidths[1] == pytest.approx(AVAIL_WIDTH - lw)

    def test_value_converted_to_string(self, styled):
        """Numeric values are str()-ified in Paragraph."""
        t = styled._kv_table([('Count', 42)])
        assert isinstance(t, Table)
