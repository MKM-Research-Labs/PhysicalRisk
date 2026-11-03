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

"""Tests for routes.cdm_review — the CDM Asset Review tool mounted in the main app.

Covers: requests under /cdm-asset-review/ reach the tool with the prefix stripped,
the bare prefix redirects to the trailing-slash URL the page's relative links need,
the rest of the app is untouched, the tool is loaded once and only on first use,
and the real tool page is served from the main app.
"""

from flask import Flask

from routes.cdm_review import PREFIX, LazyCdmReview, mount_cdm_review


def _tool():
    tool = Flask("stub_cdm_tool")

    @tool.route("/")
    def index():
        return "cdm-index"

    @tool.route("/api/assets")
    def assets():
        return {"script_root": __import__("flask").request.script_root}

    return tool


def _client(tool):
    app = Flask(__name__)

    @app.route("/visualization")
    def vis():
        return "map"

    mount_cdm_review(app, tool)
    return app.test_client()


class TestMount:

    def test_prefix_serves_tool_index(self):
        r = _client(_tool()).get(PREFIX + "/")
        assert r.status_code == 200
        assert r.get_data(as_text=True) == "cdm-index"

    def test_tool_routes_see_prefix_as_script_root(self):
        r = _client(_tool()).get(PREFIX + "/api/assets")
        assert r.get_json() == {"script_root": PREFIX}

    def test_bare_prefix_redirects_to_trailing_slash(self):
        r = _client(LazyCdmReview(loader=_tool)).get(PREFIX)
        assert r.status_code in (301, 302)
        assert r.headers["Location"].endswith(PREFIX + "/")

    def test_main_app_routes_unaffected(self):
        assert _client(_tool()).get("/visualization").get_data(as_text=True) == "map"


class TestLazyLoad:

    def test_loads_once_on_first_request(self):
        calls = []

        def loader():
            calls.append(1)
            return _tool()

        client = _client(LazyCdmReview(loader=loader))
        assert calls == []
        client.get(PREFIX + "/")
        client.get(PREFIX + "/api/assets")
        assert calls == [1]


class TestRealTool:

    def test_main_app_serves_cdm_page_with_relative_assets(self):
        client = _client(LazyCdmReview())
        page = client.get(PREFIX + "/").get_data(as_text=True)
        assert "<title>CDM Asset Review</title>" in page
        assert 'src="static/app.js"' in page
        assert client.get(PREFIX + "/static/app.js").status_code == 200
        assert client.get(PREFIX + "/shared/theme.js").status_code == 200
        assert client.get(PREFIX + "/theme.css").status_code == 200
        assert client.get(PREFIX + "/api/assets").status_code == 200
