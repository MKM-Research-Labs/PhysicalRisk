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

"""Tests for the port admin-password gate.

The gate guards the portfolio it sits beside. These cover the locator's
two resolution routes and both authentication branches, with particular
attention to the first-run branch on a fresh data root — the case that
made the throwaway-portfolio workflow impossible before the credential
followed ``MKM_DATA_ROOT``.
"""

import hashlib
import json
import os
from pathlib import Path

import pytest

from app.commands.port import auth


def _write_credential(path: Path, password: str) -> None:
    """Write a salted-hash credential file the way ``_set_password`` does."""
    salt = os.urandom(16).hex()
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    path.write_text(json.dumps({"salt": salt, "hash": h}))


class TestAdminFilePath:
    """Where the credential is looked for."""

    def test_env_override_wins(self, monkeypatch, tmp_path):
        """MKM_ADMIN_FILE_PATH takes precedence over the data root."""
        target = tmp_path / "elsewhere" / ".port_admin"
        monkeypatch.setenv("MKM_ADMIN_FILE_PATH", str(target))
        monkeypatch.setenv("MKM_DATA_ROOT", str(tmp_path / "ignored"))
        assert auth._admin_file_path() == target

    def test_follows_the_data_root(self, monkeypatch, tmp_path):
        """Without an override the credential sits in the active data root.

        This is what lets a throwaway portfolio carry its own credential
        rather than reaching for the shared volume's.
        """
        monkeypatch.delenv("MKM_ADMIN_FILE_PATH", raising=False)
        monkeypatch.setenv("MKM_DATA_ROOT", str(tmp_path))
        assert auth._admin_file_path() == tmp_path / ".port_admin"

    def test_two_data_roots_give_two_credentials(self, monkeypatch, tmp_path):
        """The locator re-reads the environment rather than caching."""
        monkeypatch.delenv("MKM_ADMIN_FILE_PATH", raising=False)
        monkeypatch.setenv("MKM_DATA_ROOT", str(tmp_path / "a"))
        first = auth._admin_file_path()
        monkeypatch.setenv("MKM_DATA_ROOT", str(tmp_path / "b"))
        assert auth._admin_file_path() != first


class TestFirstRunOnAFreshRoot:
    """The branch a newly generated throwaway portfolio takes."""

    @pytest.fixture(autouse=True)
    def _fresh_root(self, monkeypatch, tmp_path):
        monkeypatch.delenv("MKM_ADMIN_FILE_PATH", raising=False)
        monkeypatch.setenv("MKM_DATA_ROOT", str(tmp_path))
        self.root = tmp_path

    def test_creates_credential_from_the_environment(self, monkeypatch, capsys):
        """No prompt: the env var supplies the new password.

        Regression — ``_set_password`` used to ignore
        ``MKM_PORT_ADMIN_PASSWORD``, so an unattended run blocked on
        ``getpass`` with no way through.
        """
        monkeypatch.setenv("MKM_PORT_ADMIN_PASSWORD", "throwaway-pw")
        auth._authenticate()
        stored = json.loads((self.root / ".port_admin").read_text())
        expected = hashlib.sha256(
            (stored["salt"] + "throwaway-pw").encode()
        ).hexdigest()
        assert stored["hash"] == expected

    def test_never_prompts_when_the_environment_supplies_one(self, monkeypatch):
        """getpass is not reached, so a TTY-less run cannot stall."""
        monkeypatch.setenv("MKM_PORT_ADMIN_PASSWORD", "throwaway-pw")

        def _explode(*_args, **_kwargs):
            raise AssertionError("getpass called despite env password")

        monkeypatch.setattr(auth.getpass, "getpass", _explode)
        auth._authenticate()

    def test_short_env_password_is_still_rejected(self, monkeypatch):
        """The env var cannot install a weaker credential than a human could."""
        monkeypatch.setenv("MKM_PORT_ADMIN_PASSWORD", "ab")
        with pytest.raises(SystemExit):
            auth._authenticate()
        assert not (self.root / ".port_admin").exists()

    def test_creates_the_root_directory_if_absent(self, monkeypatch):
        """A data root that does not exist yet is created, not crashed on."""
        nested = self.root / "not" / "yet"
        monkeypatch.setenv("MKM_DATA_ROOT", str(nested))
        monkeypatch.setenv("MKM_PORT_ADMIN_PASSWORD", "throwaway-pw")
        auth._authenticate()
        assert (nested / ".port_admin").exists()

    def test_interactive_mismatch_exits(self, monkeypatch):
        """Typed passwords that disagree abort before anything is written."""
        monkeypatch.delenv("MKM_PORT_ADMIN_PASSWORD", raising=False)
        answers = iter(["first-pw", "second-pw"])
        monkeypatch.setattr(auth.getpass, "getpass", lambda _p: next(answers))
        with pytest.raises(SystemExit):
            auth._authenticate()
        assert not (self.root / ".port_admin").exists()

    def test_interactive_match_is_written(self, monkeypatch):
        """The typed route still works when the two entries agree."""
        monkeypatch.delenv("MKM_PORT_ADMIN_PASSWORD", raising=False)
        monkeypatch.setattr(auth.getpass, "getpass", lambda _p: "typed-pw")
        auth._authenticate()
        assert (self.root / ".port_admin").exists()


class TestVerifyAgainstAnExistingCredential:
    """The branch a real, already-provisioned portfolio takes."""

    @pytest.fixture(autouse=True)
    def _provisioned_root(self, monkeypatch, tmp_path):
        monkeypatch.delenv("MKM_ADMIN_FILE_PATH", raising=False)
        monkeypatch.setenv("MKM_DATA_ROOT", str(tmp_path))
        _write_credential(tmp_path / ".port_admin", "correct-pw")
        self.root = tmp_path

    def test_correct_env_password_passes(self, monkeypatch):
        monkeypatch.setenv("MKM_PORT_ADMIN_PASSWORD", "correct-pw")
        auth._authenticate()

    def test_wrong_env_password_exits(self, monkeypatch):
        """A wrong value fails — the gate is exercised, not skipped."""
        monkeypatch.setenv("MKM_PORT_ADMIN_PASSWORD", "wrong-pw")
        with pytest.raises(SystemExit):
            auth._authenticate()

    def test_correct_typed_password_passes(self, monkeypatch, capsys):
        monkeypatch.delenv("MKM_PORT_ADMIN_PASSWORD", raising=False)
        monkeypatch.setattr(auth.getpass, "getpass", lambda _p: "correct-pw")
        auth._authenticate()
        assert "Authenticated" in capsys.readouterr().out

    def test_wrong_typed_password_exits(self, monkeypatch):
        monkeypatch.delenv("MKM_PORT_ADMIN_PASSWORD", raising=False)
        monkeypatch.setattr(auth.getpass, "getpass", lambda _p: "nope")
        with pytest.raises(SystemExit):
            auth._authenticate()

    def test_existing_credential_is_not_overwritten(self, monkeypatch):
        """Authenticating leaves the stored hash exactly as it was."""
        before = (self.root / ".port_admin").read_text()
        monkeypatch.setenv("MKM_PORT_ADMIN_PASSWORD", "correct-pw")
        auth._authenticate()
        assert (self.root / ".port_admin").read_text() == before
