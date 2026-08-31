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

global.fetch = jest.fn();

// Mock console methods to avoid noise but allow assertions
global.console = {
  ...console,
  log: jest.fn(),
  error: jest.fn(),
  warn: jest.fn()
};

// Leaflet stubs
global.L = {
  Marker: class Marker {
    constructor() {
      this._hasContextMenu = false;
      this._markerId = null;
      this._markerType = null;
    }
    on() { return this; }
    getTooltip() { return null; }
    getPopup() { return null; }
    openPopup() {}
  }
};

// CustomEvent polyfill for jsdom
if (typeof global.CustomEvent !== 'function') {
  global.CustomEvent = class CustomEvent extends Event {
    constructor(type, params) {
      params = params || {};
      super(type, params);
      this.detail = params.detail || null;
    }
  };
}

// --- Design tokens (coding rule R7) -----------------------------------------
//
// The console injects the :root block and theme.js as the first element in the body,
// ahead of every panel script, so Theme is always defined by the time any of them run.
// A unit test that requires a panel module in isolation has no such page, so the setup
// builds the same thing: the real token values from config/theme, applied to the
// document root, then the real theme.js on top.
//
// Reading the tokens from the emitted stylesheet rather than restating them here is
// deliberate — a fixture that lists its own colours is a second palette, and it would
// drift from the first the moment anyone renamed a token.
const { execFileSync } = require('child_process');
const path = require('path');

const repoRoot = path.resolve(__dirname, '../..');
let themeCss = '';
try {
  // config/__init__.py builds a PortfolioConfig at import time, which mkdirs into the
  // data/ symlink — an external disk. Importing it here would make the JavaScript unit
  // tests fail whenever that disk is unmounted, for tokens that have nothing to do with
  // it. Stubbing the parent package loads config.theme alone, off the repo only.
  themeCss = execFileSync(
    'python3',
    ['-c',
     'import sys, types, pathlib\n'
     + 'root = pathlib.Path(".").resolve()\n'
     + 'sys.path.insert(0, str(root))\n'
     + 'pkg = types.ModuleType("config")\n'
     + 'pkg.__path__ = [str(root / "config")]\n'
     + 'sys.modules["config"] = pkg\n'
     + 'from config.theme import THEME_GROUPS\n'
     + 'print(":root {")\n'
     + '[print(f"  --{n}: {v};") for _, g in THEME_GROUPS for n, v in g.items()]\n'
     + 'print("}")'],
    { cwd: repoRoot, encoding: 'utf8' });
} catch (err) {
  // Python unavailable entirely. The tests that assert a resolved colour then fail
  // loudly rather than silently passing against an empty palette, which is the right
  // way round — a green suite that proved nothing is worse than a red one.
  themeCss = '';
}

const style = document.createElement('style');
style.textContent = themeCss;
document.head.appendChild(style);

// jsdom does not resolve custom properties from a <style> block, so apply them to the
// root element's inline style, which it does resolve.
for (const match of themeCss.matchAll(/--([a-z0-9-]+):\s*([^;]+);/g)) {
  document.documentElement.style.setProperty('--' + match[1], match[2].trim());
}

require('../../src/static/js/theme.js');
