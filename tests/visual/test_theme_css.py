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
from visual.theme_css import (
    THEME_STYLE_ID, theme_css, theme_html, theme_status_js, token_names,
)

_DECLARATION = re.compile(r"^\s*--([a-z0-9-]+):\s*(.+);$", re.MULTILINE)
_VAR_REFERENCE = re.compile(r"var\(\s*--([a-zA-Z0-9_-]+)")

# Documents that are not the Folium console and so do not receive the manager's
# injection: each is self-contained, carries its own ``:root``, and gets its own
# emitter in a later step. Named here rather than skipped silently, so the day one of
# them is converted the omission is visible.
# Every document is served the shared tokens now — the admin page and the CDM tool both
# link /theme.css since step 4 — so nothing is exempt from the resolution check.
SELF_CONTAINED_DOCUMENTS = ()


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

    def test_nothing_is_exempt_from_token_resolution(self):
        """Step 4 served every document the shared block; the list should stay empty."""
        assert SELF_CONTAINED_DOCUMENTS == ()


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


class TestStatusRampsReachTheBrowser:
    """``window.__THEME_STATUS`` — the ramps the front end reads by name.

    The load-bearing test is :meth:`test_every_js_ramp_reference_exists`. A ramp name
    typo'd in JavaScript fails the same silent way an undefined token does: the lookup
    yields an empty object, every badge falls through to its ``||`` default, and a whole
    panel quietly goes grey on a screen nobody happened to open.
    """

    def test_payload_is_valid_json(self):
        import json

        payload = theme_status_js()
        assert payload.startswith("window.__THEME_STATUS = ")
        body = payload[len("window.__THEME_STATUS = "):].rstrip(";")
        json.loads(body)

    def test_carries_every_ramp_family(self):
        import json

        from config.theme import STATUS_COLOUR_TOKENS

        body = theme_status_js()[len("window.__THEME_STATUS = "):].rstrip(";")
        ramps = json.loads(body)["ramps"]
        assert set(ramps) == set(STATUS_COLOUR_TOKENS)

    def test_carries_the_per_ramp_defaults(self):
        """The browser must fall back the same way Python does."""
        import json

        from config.theme import STATUS_COLOUR_DEFAULTS

        body = theme_status_js()[len("window.__THEME_STATUS = "):].rstrip(";")
        assert json.loads(body)["defaults"] == STATUS_COLOUR_DEFAULTS

    def test_emits_token_names_not_colours(self):
        """A second copy of the palette here could drift from the :root block."""
        import json

        body = theme_status_js()[len("window.__THEME_STATUS = "):].rstrip(";")
        for ramp, mapping in json.loads(body)["ramps"].items():
            for value, token in mapping.items():
                assert not token.startswith("#"), f"{ramp}[{value}] is a colour"
                assert token in THEME, f"{ramp}[{value}] -> {token} is not a token"

    def test_every_js_ramp_reference_exists(self, repo_root):
        """Every Theme.ramp('x') in the front end names a ramp the emitter defines."""
        import json
        import re as _re

        body = theme_status_js()[len("window.__THEME_STATUS = "):].rstrip(";")
        defined = set(json.loads(body)["ramps"])
        pattern = _re.compile(r"Theme\.(?:ramp|status|statusRef)\(\s*['\"]([\w]+)['\"]")
        unknown = []
        for path in (repo_root / "src" / "static" / "js").rglob("*.js"):
            if path.name == "theme.js":
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                for name in pattern.findall(line):
                    if name not in defined:
                        unknown.append(f"{path.relative_to(repo_root)}:{number} {name}")
        assert unknown == [], "unknown ramp names: " + ", ".join(unknown)

    def test_status_payload_precedes_theme_js_in_the_page(self):
        """theme.js reads window.__THEME_STATUS; it must already be assigned."""
        html = theme_html()
        assert html.index("window.__THEME_STATUS") < html.index("window.Theme")


class TestStylesheetsAreTokenised:
    """No colour literal survives in a stylesheet or a served HTML document.

    Step 5 gates these at zero, so this is the check that keeps them there. The
    JavaScript backlog is deliberately not included — it is step 6's work and is
    reported by count rather than gated.
    """

    #: Every stylesheet and standalone document the platform serves.
    STYLE_SURFACES = (
        "src/static/css/context-menus.css",
        "src/static/css/nav-menus.css",
        "src/static/css/notifications.css",
        "src/static/admin/admin.html",
        "tools/cdm_property_editor/static/styles.css",
    )

    _LITERAL = re.compile(
        r"#[0-9a-fA-F]{3,6}\b"          # hex
        r"|rgba?\([0-9.,\s]+\)"          # rgb/rgba
        r"|(?<=[:\s])(?:white|black)(?=[;\s,)])"  # bare keywords
    )

    def test_no_colour_literals_remain(self, repo_root):
        offenders = []
        for relative in self.STYLE_SURFACES:
            path = repo_root / relative
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if line.lstrip().startswith(("/*", "*", "//")):
                    continue
                for hit in self._LITERAL.findall(line):
                    offenders.append(f"{relative}:{number} {hit}")
        assert offenders == [], "colour literals outside config: " + ", ".join(offenders)

    def test_every_token_they_use_is_defined(self, repo_root):
        """A ``var()`` naming nothing renders as an inherited colour, silently."""
        unresolved = []
        for relative in self.STYLE_SURFACES:
            text = (repo_root / relative).read_text(encoding="utf-8")
            for token in set(re.findall(r"var\(--([a-z0-9-]+)\)", text)):
                if token not in THEME:
                    unresolved.append(f"{relative} --{token}")
        assert unresolved == [], "undefined tokens: " + ", ".join(unresolved)

    def test_the_surfaces_still_exist(self, repo_root):
        """So the list cannot rot into a blanket pass."""
        for relative in self.STYLE_SURFACES:
            assert (repo_root / relative).is_file(), relative

    def test_no_surface_carries_its_own_root_block(self, repo_root):
        """A local ``:root`` is a second place the appearance gets decided.

        Both the CDM tool and the admin page used to define one; they are served
        ``/theme.css`` now. A new one would silently shadow the shared tokens.
        """
        for relative in self.STYLE_SURFACES:
            text = (repo_root / relative).read_text(encoding="utf-8")
            assert ":root" not in text, f"{relative} defines its own :root"
