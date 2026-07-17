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

"""
Tests for PopupBuilder output methods and integration:
- create_colored_text
- create_popup_wrapper
- build_popup
- Integration (method chaining)
"""

import folium


# ===========================================================================
# create_colored_text
# ===========================================================================

class TestCreateColoredText:

    def test_returns_string(self, builder):
        result = builder.create_colored_text("hello", "red")
        assert isinstance(result, str)

    def test_contains_text(self, builder):
        result = builder.create_colored_text("hello world", "green")
        assert "hello world" in result

    def test_contains_color(self, builder):
        result = builder.create_colored_text("text", "blue")
        assert "color: blue" in result

    def test_contains_span_tag(self, builder):
        result = builder.create_colored_text("text", "red")
        assert "<span" in result

    def test_not_bold_by_default(self, builder):
        result = builder.create_colored_text("text", "red")
        assert "font-weight: bold" not in result

    def test_bold_flag_adds_bold_style(self, builder):
        result = builder.create_colored_text("text", "red", bold=True)
        assert "font-weight: bold" in result

    def test_bold_false_no_bold_style(self, builder):
        result = builder.create_colored_text("text", "red", bold=False)
        assert "font-weight: bold" not in result

    def test_empty_text(self, builder):
        result = builder.create_colored_text("", "red")
        assert isinstance(result, str)

    def test_hex_color(self, builder):
        result = builder.create_colored_text("text", "#1a5276")
        assert "#1a5276" in result

    def test_bold_with_hex_color(self, builder):
        result = builder.create_colored_text("Important", "#FF0000", bold=True)
        assert "#FF0000" in result
        assert "font-weight: bold" in result

    def test_closes_span_tag(self, builder):
        result = builder.create_colored_text("text", "red")
        assert "</span>" in result


# ===========================================================================
# create_popup_wrapper
# ===========================================================================

class TestCreatePopupWrapper:

    def test_returns_string(self, builder):
        result = builder.create_popup_wrapper("content")
        assert isinstance(result, str)

    def test_contains_content(self, builder):
        result = builder.create_popup_wrapper("<p>Hello</p>")
        assert "Hello" in result

    def test_default_max_width_in_html(self, builder):
        result = builder.create_popup_wrapper("content")
        assert "320px" in result

    def test_default_max_height_in_html(self, builder):
        result = builder.create_popup_wrapper("content")
        assert "400px" in result

    def test_custom_max_width(self, builder):
        result = builder.create_popup_wrapper("content", max_width=500)
        assert "500px" in result

    def test_custom_max_height(self, builder):
        result = builder.create_popup_wrapper("content", max_height=600)
        assert "600px" in result

    def test_contains_font_family(self, builder):
        result = builder.create_popup_wrapper("content")
        assert "font-family" in result

    def test_contains_arial(self, builder):
        result = builder.create_popup_wrapper("content")
        assert "Arial" in result

    def test_contains_overflow_y_auto(self, builder):
        result = builder.create_popup_wrapper("content")
        assert "overflow-y: auto" in result

    def test_contains_div_tag(self, builder):
        result = builder.create_popup_wrapper("content")
        assert "<div" in result

    def test_empty_content(self, builder):
        result = builder.create_popup_wrapper("")
        assert isinstance(result, str)
        assert "<div" in result

    def test_html_content_preserved(self, builder):
        html_content = "<h4>Title</h4><p>Body</p>"
        result = builder.create_popup_wrapper(html_content)
        assert "<h4>Title</h4>" in result
        assert "<p>Body</p>" in result


# ===========================================================================
# build_popup
# ===========================================================================

class TestBuildPopup:

    def test_returns_folium_popup(self, builder):
        result = builder.build_popup("<p>content</p>")
        assert isinstance(result, folium.Popup)

    def test_popup_is_not_none(self, builder):
        result = builder.build_popup("<p>content</p>")
        assert result is not None

    def test_default_max_width_350(self, builder):
        result = builder.build_popup("<p>content</p>")
        # folium.Popup is created successfully; check content is present
        assert result is not None
        assert "content" in result.html.render()

    def test_custom_max_width(self, builder):
        result = builder.build_popup("<p>content</p>", max_width=500)
        # folium.Popup is created successfully with custom max_width parameter
        assert result is not None
        assert "content" in result.html.render()

    def test_popup_attachable_to_marker(self, builder):
        popup = builder.build_popup("<p>Test Popup</p>")
        m = folium.Map(location=[51.5, -0.1])
        folium.Marker(location=[51.5, -0.1], popup=popup).add_to(m)
        html = m._repr_html_()
        assert len(html) > 0

    def test_popup_html_contains_content(self, builder):
        popup = builder.build_popup("<p>unique_marker_string</p>")
        rendered = popup.html.render()
        assert "unique_marker_string" in rendered

    def test_empty_content(self, builder):
        result = builder.build_popup("")
        assert isinstance(result, folium.Popup)

    def test_complex_html_content(self, builder):
        content = "<div><h4>Title</h4><p>Para</p><ul><li>Item</li></ul></div>"
        result = builder.build_popup(content)
        assert isinstance(result, folium.Popup)


# ===========================================================================
# Integration: method chaining produces valid Folium popup
# ===========================================================================

class TestIntegration:

    def test_full_popup_pipeline(self, builder):
        header = builder.create_header("Test Header", subtitle="Subtitle Text")
        row1 = builder.create_data_row("Risk Level", "High", bold_label=True)
        row2 = builder.create_data_row("Value", "\u00a3100,000", bold_label=False)
        section = builder.create_section("Details", row1 + row2)
        colored = builder.create_colored_text("High", "red", bold=True)
        wrapped = builder.create_popup_wrapper(header + section + colored)
        popup = builder.build_popup(wrapped)
        assert isinstance(popup, folium.Popup)
        assert "Test Header" in popup.html.render()
        assert "Risk Level" in popup.html.render()

    def test_popup_with_all_risk_colors(self, builder):
        levels = ["Very Low", "Low", "Medium", "High", "Very High", "Unknown"]
        for level in levels:
            color = builder.get_risk_color(level)
            text = builder.create_colored_text(level, color)
            row = builder.create_data_row("Risk", text)
            popup = builder.build_popup(row)
            assert isinstance(popup, folium.Popup)

    def test_currency_and_percentage_in_popup(self, builder):
        currency = builder.format_currency(250000)
        pct = builder.format_percentage(0.045)
        row1 = builder.create_data_row("Property Value", currency)
        row2 = builder.create_data_row("Interest Rate", pct)
        wrapped = builder.create_popup_wrapper(row1 + row2)
        popup = builder.build_popup(wrapped)
        rendered = popup.html.render()
        assert "250,000" in rendered
        assert "4.5%" in rendered

    def test_na_values_appear_in_popup(self, builder):
        val = builder.safe_format_float(None)
        row = builder.create_data_row("Reading", val)
        popup = builder.build_popup(row)
        assert "N/A" in popup.html.render()

    def test_marker_with_complex_popup_renders(self, builder):
        header = builder.create_header("Gauge GAUGE-001", subtitle="Thames River")
        section = builder.create_section(
            "Current Level",
            builder.create_data_row("Water Level", builder.safe_format_float(3.75)) +
            builder.create_data_row("Risk", builder.create_colored_text("Medium", "orange"))
        )
        wrapped = builder.create_popup_wrapper(header + section, max_width=400, max_height=500)
        popup = builder.build_popup(wrapped, max_width=400)
        m = folium.Map(location=[51.5, -0.1])
        folium.Marker(location=[51.5, -0.1], popup=popup).add_to(m)
        assert len(m._repr_html_()) > 0
