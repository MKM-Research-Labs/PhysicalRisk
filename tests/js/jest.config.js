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

module.exports = {
  rootDir: '../../',
  testEnvironment: 'jsdom',
  testMatch: ['**/tests/js/**/*.test.js'],
  // rootDir is the repo root so coverage can reach src/static/js, but that
  // also puts .claude/worktrees/ inside testMatch's reach — jest would collect
  // stale copies of these same files from other branches and run them against
  // this checkout's source (306 tests instead of 87, with failures owned by
  // whichever branch happens to be checked out elsewhere). `roots` scopes
  // DISCOVERY to this checkout's own tests while leaving rootDir alone for
  // coverage. Note an ignore pattern on '.claude' cannot do this job: a
  // worktree lives *inside* .claude/worktrees/, so it would discard the
  // worktree's own tests when run from there.
  roots: ['<rootDir>/tests/js'],
  setupFiles: ['<rootDir>/tests/js/setup.js']
};
