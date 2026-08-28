// Copyright (c) 2022-2026 MKM Research Labs.
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

// Theme — read access to the design tokens defined in config/theme.
//
// The tokens arrive as a :root custom-property block that src/visual/theme_css.py
// injects immediately above this script, so they are already in the cascade by the
// time anything here runs. CSS and HTML style attributes should use var(--token)
// directly and never come through this object at all.
//
// This exists for the callers that CANNOT use var(): Chart.js datasets, Leaflet path
// options and SVG presentation attributes are JavaScript values or XML attributes,
// not CSS declarations, and none of them resolve a custom property. fill="var(--red)"
// renders black, silently. Those sites take Theme.value(token) instead.
//
// Reading back off the cascade rather than being handed a second copy of the values
// is deliberate: one payload cannot disagree with itself, and the browser stays the
// single authority on what a token resolves to.
window.Theme = window.Theme || (function () {
  var cache = {};

  // getComputedStyle is not free and the chart builders ask for the same handful of
  // tokens per redraw, so each token is resolved once per page.
  function resolve(token) {
    if (Object.prototype.hasOwnProperty.call(cache, token)) return cache[token];
    var raw = getComputedStyle(document.documentElement)
      .getPropertyValue('--' + token);
    cache[token] = raw ? raw.trim() : null;
    return cache[token];
  }

  return {
    // The literal value a token resolves to ("#1976d2"), or null when the theme
    // does not define it. Null rather than a fallback colour on purpose: a caller
    // that silently substitutes one paints an unthemed element in a plausible
    // colour, which is exactly the failure the R7 token check exists to catch.
    value: function (token) { return resolve(token); },

    // A token as CSS refers to it. For building a style attribute in JavaScript,
    // where var() does resolve normally.
    ref: function (token) { return token ? 'var(--' + token + ')' : null; },

    // Whether the theme defines a token. Lets a caller fail loudly in development
    // rather than draw with null.
    has: function (token) { return resolve(token) !== null; },

    // Drop the memo. Only of use to a test that swaps the :root block underneath a
    // live page; nothing in the console changes its theme at runtime today.
    reset: function () { cache = {}; },
  };
}());
