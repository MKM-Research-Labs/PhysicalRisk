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

"""The e2e phase clears the previous run's artefacts before writing its own.

Batch JUnit files are named by index, so without this a run producing fewer
batches than its predecessor leaves the extras behind and they read as part of
this run. A run that dies partway is worse: it overwrites some batches and not
others while e2e_results.json still describes the earlier run, so the summary
names failures whose detail no longer exists.

Observed on 2026-09-04 — three runs' batches in one directory, a results.json
two days older than most of them, and 15 of one run's 22 batch files
overwritten by a later partial run.
"""

from app.commands.test.e2e import _clear_previous_artefacts, _unlink_quietly


def _populate(d):
    for name in ("e2e_junit.xml", "e2e_junit_batch1.xml",
                 "e2e_junit_batch17.xml", "e2e_results.json"):
        (d / name).write_text("stale")
    return sorted(p.name for p in d.iterdir())


class TestClearPreviousArtefacts:

    def test_batch_and_summary_artefacts_are_removed(self, tmp_path):
        _populate(tmp_path)
        _clear_previous_artefacts(str(tmp_path))
        assert list(tmp_path.iterdir()) == []

    def test_a_high_numbered_batch_cannot_survive_a_shorter_run(self, tmp_path):
        """The failure this exists to prevent: batch17 from a 22-batch run
        outliving a later 8-batch run and being read as part of it."""
        (tmp_path / "e2e_junit_batch17.xml").write_text("<testsuite/>")
        _clear_previous_artefacts(str(tmp_path))
        assert not (tmp_path / "e2e_junit_batch17.xml").exists()

    def test_unrelated_files_are_left_alone(self, tmp_path):
        """Only this phase's own artefacts. The js/ subfolder and any
        coverage output live alongside and belong to other phases."""
        (tmp_path / "js_results.json").write_text("keep")
        (tmp_path / "coverage.xml").write_text("keep")
        (tmp_path / "notes.txt").write_text("keep")
        _populate(tmp_path)

        _clear_previous_artefacts(str(tmp_path))

        assert sorted(p.name for p in tmp_path.iterdir()) == [
            "coverage.xml", "js_results.json", "notes.txt"]

    def test_an_empty_directory_is_fine(self, tmp_path):
        _clear_previous_artefacts(str(tmp_path))
        assert list(tmp_path.iterdir()) == []

    def test_a_subdirectory_is_not_removed(self, tmp_path):
        """os.remove on a directory raises; the helper must not trip on one
        that happens to match the name pattern."""
        (tmp_path / "e2e_junit_batch1.xml").mkdir()
        _clear_previous_artefacts(str(tmp_path))
        assert (tmp_path / "e2e_junit_batch1.xml").is_dir()


class TestUnlinkQuietly:

    def test_a_missing_file_is_not_an_error(self, tmp_path):
        """Another process clearing the same directory must not fail the run."""
        _unlink_quietly(str(tmp_path / "gone.xml"))

    def test_an_existing_file_is_removed(self, tmp_path):
        f = tmp_path / "here.xml"
        f.write_text("x")
        _unlink_quietly(str(f))
        assert not f.exists()
