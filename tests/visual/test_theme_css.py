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

"""Tests for src.visual.theme_css — the emitted token block (coding rule R7).

The load-bearing test in this file is
:meth:`TestTokenResolution.test_every_var_reference_resolves`. A colour literal left
behind is visible in a diff; a ``var(--token)`` naming a token that does not exist is
not — the browser drops the declaration in silence and the element renders with
whatever it inherits, so a rename reaches a screen as a colour quietly falling back,
on whichever panel nobody happened to open. It passes trivially today because the
console has no ``var()`` references yet, and becomes the guard rail as step 6 of
docs/refactor/theme_centralisation_plan.md converts them.
"""

import re

import pytest

from config import config
from config.theme import THEME, THEME_GROUPS
from visual.theme_css import THEME_STYLE_ID, theme_css, theme_html, token_names

_DECLARATION = re.compile(r"^\s*--([a-z0-9-]+):\s*(.+);$", re.MULTILINE)
_VAR_REFERENCE = re.compile(r"var\(\s*--([a-zA-Z0-9_-]+)")

# Documents that are not the Folium console and so do not receive the manager's
# injection: each is self-contained, carries its own ``:root``, and gets its own
# emitter in a later step. Named here rather than skipped silently, so the day one of
# them is converted the omission is visible.
SELF_CONTAINED_DOCUMENTS = (
    "src/static/admin/admin.html",
)


@pytest.fixture(scope="module")
def repo_root():
    """The checkout root, from the config accessor rather than walked by hand."""
    return config.get_project_root()


class TestThemeCss:
    def test_is_a_single_root_block(self):
        css = theme_css()
        assert css.startswith(":root {")
        assert css.rstrip().endswith("}")
        assert css.count(":root") == 1

    def test_declares_every_token_exactly_once(self):
        declared = _DECLARATION.findall(theme_css())
        assert declared, "the declaration regex matched nothing"
        names = [name for name, _ in declared]
        assert sorted(names) == sorted(THEME)
        assert len(names) == len(set(names))

    def test_declared_values_match_the_config(self):
        declared = _DECLARATION.findall(theme_css())
        assert len(declared) == len(THEME)
        for name, value in declared:
            assert value == THEME[name], f"--{name} emitted as {value!r}"

    def test_groups_are_emitted_in_registry_order(self):
        """The block reads the way the package does, so a diff of either is legible."""
        css = theme_css()
        positions = [css.index(f"/* {label} */") for label, _ in THEME_GROUPS]
        assert positions == sorted(positions)

    def test_every_group_is_labelled(self):
        css = theme_css()
        for label, _ in THEME_GROUPS:
            assert f"/* {label} */" in css

    def test_token_names_helper_matches_the_theme(self):
        assert set(token_names()) == set(THEME)


class TestThemeHtml:
    def test_carries_the_style_block_and_the_script(self):
        html = theme_html()
        assert f'<style id="{THEME_STYLE_ID}">' in html
        assert "</style>" in html
        assert "<script>" in html and "</script>" in html

    def test_style_precedes_the_script(self):
        """The properties must be in the cascade before anything reads one."""
        html = theme_html()
        assert html.index("</style>") < html.index("<script>")

    def test_script_is_the_theme_helper(self):
        assert "window.Theme" in theme_html()

    def test_carries_no_stray_selector(self):
        """A serialiser of configuration, not a stylesheet.

        Rules belong in ``src/static/css``; anything else here would be a second,
        invisible place for the console's appearance to be decided.
        """
        style = theme_html().split("</style>")[0]
        assert style.count("{") == 1


class TestTokenResolution:
    """Every ``var(--token)`` the console reads resolves to a token that exists."""

    @staticmethod
    def _console_assets(repo_root):
        for suffix in ("*.js", "*.css", "*.html"):
            for path in (repo_root / "src" / "static").rglob(suffix):
                if str(path.relative_to(repo_root)) in SELF_CONTAINED_DOCUMENTS:
                    continue
                yield path

    def test_every_var_reference_resolves(self, repo_root):
        unresolved = []
        for path in self._console_assets(repo_root):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                for token in _VAR_REFERENCE.findall(line):
                    # theme.js builds a reference from a runtime argument; the string
                    # 'var(--' + token is not itself a reference to a token.
                    if path.name == "theme.js":
                        continue
                    if token not in THEME:
                        unresolved.append(f"{path.relative_to(repo_root)}:{number} --{token}")
        assert unresolved == [], "undefined design tokens: " + ", ".join(unresolved)

    def test_self_contained_documents_still_exist(self, repo_root):
        """The exemption list names real files, so it cannot rot into a blanket pass."""
        for relative in SELF_CONTAINED_DOCUMENTS:
            assert (repo_root / relative).is_file(), f"{relative} no longer exists"


class TestRenderedPage:
    """The tokens reach an actual console page, not just the emitter's return value."""

    @staticmethod
    def _rendered():
        import folium

        from visual.interactivity.manager import InteractivityManager

        folium_map = folium.Map(location=[51.5, -0.1], zoom_start=10)
        InteractivityManager().setup_map_interactivity(folium_map)
        return folium_map.get_root().render()

    def test_every_token_reaches_the_page(self):
        html = self._rendered()
        declared = _DECLARATION.findall(html)
        assert {name for name, _ in declared} == set(THEME)

    def test_block_precedes_every_console_stylesheet(self):
        """First in the body, so a panel redefining a token overrides the theme.

        The blocks Folium emits into ``<head>`` are Leaflet's own and are not part of
        the console's styling, so the comparison starts at ``<body>``.
        """
        html = self._rendered()
        body = html[html.index("<body"):]
        assert body.index(f'id="{THEME_STYLE_ID}"') < body.index("<style>")

    def test_license_header_is_not_rendered_as_text(self):
        """theme.js is inlined raw; a leading ``//`` block would show on the map.

        The console has shipped this bug before — see the js_static header strip.
        """
        html = self._rendered()
        after_style = html.split("</style>", 1)[1]
        assert "Permission is hereby granted" not in after_style[:4000]

    def test_theme_helper_is_available_to_panel_scripts(self):
        assert "window.Theme" in self._rendered()
