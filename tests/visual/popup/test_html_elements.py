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
Tests for PopupBuilder HTML element methods:
- Instantiation
- create_section
- create_header
- create_data_row
"""

from visual.popups.popup_builder import PopupBuilder


# ===========================================================================
# Instantiation
# ===========================================================================

class TestPopupBuilderInstantiation:

    def test_can_be_instantiated(self):
        b = PopupBuilder()
        assert b is not None

    def test_is_correct_type(self):
        b = PopupBuilder()
        assert isinstance(b, PopupBuilder)


# ===========================================================================
# create_section
# ===========================================================================

class TestCreateSection:

    def test_returns_string(self, builder):
        result = builder.create_section("My Title", "My Content")
        assert isinstance(result, str)

    def test_contains_title(self, builder):
        result = builder.create_section("Section Title", "some content")
        assert "Section Title" in result

    def test_contains_content(self, builder):
        result = builder.create_section("Title", "<p>Hello World</p>")
        assert "Hello World" in result

    def test_default_background_color_in_html(self, builder):
        result = builder.create_section("T", "C")
        assert "#EBF5FB" in result

    def test_default_title_color_in_html(self, builder):
        result = builder.create_section("T", "C")
        assert "#1a5276" in result

    def test_custom_background_color(self, builder):
        result = builder.create_section("T", "C", background_color="#FF0000")
        assert "#FF0000" in result

    def test_custom_title_color(self, builder):
        result = builder.create_section("T", "C", title_color="#00FF00")
        assert "#00FF00" in result

    def test_both_custom_colors(self, builder):
        result = builder.create_section("T", "C", background_color="#aabbcc", title_color="#112233")
        assert "#aabbcc" in result
        assert "#112233" in result

    def test_empty_title_and_content(self, builder):
        result = builder.create_section("", "")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_html_in_content_preserved(self, builder):
        result = builder.create_section("T", "<strong>bold text</strong>")
        assert "<strong>bold text</strong>" in result

    def test_contains_h5_tag(self, builder):
        result = builder.create_section("My Section", "data")
        assert "<h5" in result

    def test_contains_div_tag(self, builder):
        result = builder.create_section("My Section", "data")
        assert "<div" in result


# ===========================================================================
# create_header
# ===========================================================================

class TestCreateHeader:

    def test_returns_string(self, builder):
        result = builder.create_header("Main Title")
        assert isinstance(result, str)

    def test_contains_title(self, builder):
        result = builder.create_header("My Title")
        assert "My Title" in result

    def test_no_subtitle_by_default(self, builder):
        result = builder.create_header("Title Only")
        assert "<p" not in result

    def test_with_subtitle_present(self, builder):
        result = builder.create_header("Title", subtitle="A subtitle")
        assert "A subtitle" in result

    def test_with_subtitle_has_paragraph_tag(self, builder):
        result = builder.create_header("Title", subtitle="Sub")
        assert "<p" in result

    def test_empty_subtitle_treated_as_no_subtitle(self, builder):
        result = builder.create_header("Title", subtitle="")
        # empty string is falsy — no subtitle rendered
        assert "<p" not in result

    def test_default_main_color_in_html(self, builder):
        result = builder.create_header("Title")
        assert "#1a5276" in result

    def test_custom_main_color(self, builder):
        result = builder.create_header("Title", main_color="#abcdef")
        assert "#abcdef" in result

    def test_contains_h4_tag(self, builder):
        result = builder.create_header("Title")
        assert "<h4" in result

    def test_subtitle_has_color_style(self, builder):
        result = builder.create_header("Title", subtitle="Some subtitle")
        assert "#566573" in result


# ===========================================================================
# create_data_row
# ===========================================================================

class TestCreateDataRow:

    def test_returns_string(self, builder):
        result = builder.create_data_row("Label", "Value")
        assert isinstance(result, str)

    def test_contains_label(self, builder):
        result = builder.create_data_row("My Label", "My Value")
        assert "My Label" in result

    def test_contains_value(self, builder):
        result = builder.create_data_row("Label", "123.45")
        assert "123.45" in result

    def test_bold_label_default(self, builder):
        result = builder.create_data_row("Label", "Value")
        assert "font-weight: bold" in result

    def test_non_bold_label(self, builder):
        result = builder.create_data_row("Label", "Value", bold_label=False)
        assert "font-weight: bold" not in result

    def test_contains_p_tag(self, builder):
        result = builder.create_data_row("Label", "Value")
        assert "<p>" in result or "<p " in result

    def test_contains_span_tag(self, builder):
        result = builder.create_data_row("Label", "Value")
        assert "<span" in result

    def test_label_has_colon(self, builder):
        result = builder.create_data_row("Field", "data")
        assert "Field:" in result

    def test_numeric_value_rendered(self, builder):
        result = builder.create_data_row("Count", 42)
        assert "42" in result

    def test_float_value_rendered(self, builder):
        result = builder.create_data_row("Rate", 3.14)
        assert "3.14" in result

    def test_none_value_rendered(self, builder):
        result = builder.create_data_row("X", None)
        assert "None" in result

    def test_empty_label(self, builder):
        result = builder.create_data_row("", "Value")
        assert isinstance(result, str)
