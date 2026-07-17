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
