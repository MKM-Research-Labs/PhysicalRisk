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
  var rampCache = {};

  // The token a ramp falls back to for a value it does not carry. Per-ramp rather than
  // one global answer, matching config.theme.STATUS_COLOUR_DEFAULTS: a missing trigger
  // level should read as muted, a missing governance rating as grey. A ramp with no
  // entry here has no default, and an unrecognised value on it is a programming error.
  function defaultFor(ramp) {
    return ((window.__THEME_STATUS || {}).defaults || {})[ramp];
  }

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

    // The colour a business value is drawn in: Theme.status('rag_rating', 'Amber').
    //
    // The ramps come from config/theme — _status.py for the modelled world, _badges.py
    // for the console's own workflow states — and hold token names, not colours. This
    // is what replaced the 23 object literals that used to be scattered through these
    // files, five of which were different spellings of alert/warning/severe.
    //
    // An unrecognised value falls back to one shared token so an unknown state looks
    // the same everywhere. An unrecognised RAMP returns null, because that is a
    // programming error rather than missing data and should not quietly paint grey.
    status: function (ramp, value) {
        var all = (window.__THEME_STATUS || {}).ramps || {};
        if (!Object.prototype.hasOwnProperty.call(all, ramp)) return null;
        var token = all[ramp][value];
        if (token === undefined) token = defaultFor(ramp);
        return token ? resolve(token) : null;
    },

    // A whole ramp, resolved: Theme.ramp('rag_rating') -> {Green: '#388e3c', ...}.
    //
    // This is the shape the call sites already had — they were object literals keyed
    // by status, read as map[value] || fallback — so converting one is a single-line
    // change and the surrounding code is untouched. Returns an empty object for an
    // unknown ramp rather than undefined, so a lookup against it still yields
    // undefined and the caller's own || fallback keeps working.
    ramp: function (name) {
        if (Object.prototype.hasOwnProperty.call(rampCache, name)) return rampCache[name];
        var tokens = ((window.__THEME_STATUS || {}).ramps || {})[name];
        var out = {};
        if (tokens) {
            for (var value in tokens) {
                if (Object.prototype.hasOwnProperty.call(tokens, value)) {
                    out[value] = resolve(tokens[value]);
                }
            }
        }
        rampCache[name] = out;
        return out;
    },

    // The same lookup as a var() reference, for building a style attribute.
    statusRef: function (ramp, value) {
        var all = (window.__THEME_STATUS || {}).ramps || {};
        if (!Object.prototype.hasOwnProperty.call(all, ramp)) return null;
        var token = all[ramp][value];
        if (token === undefined) token = defaultFor(ramp);
        return token ? 'var(--' + token + ')' : null;
    },

    // Drop the memo. Only of use to a test that swaps the :root block underneath a
    // live page; nothing in the console changes its theme at runtime today.
    reset: function () { cache = {}; rampCache = {}; },
  };
}());
