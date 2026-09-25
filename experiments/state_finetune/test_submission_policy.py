"""A paused submission must stop before artifact I/O, credentials, or network."""

import re
import subprocess
import sys

import pytest

import submit


def test_paused_submission_stops_before_any_external_work(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Paused submission attempted artifact I/O or a process")

    monkeypatch.setattr(submit.Path, "read_text", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(sys, "argv", ["submit.py", "--work", str(tmp_path),
                                     "--artifact", str(tmp_path / "absent.vcc")])
    with pytest.raises(SystemExit, match="submissions are paused"):
        submit.main()
    assert not list(tmp_path.iterdir())


def test_public_names_are_opaque_and_generated_per_submission():
    names = [submit.new_public_name() for _ in range(32)]
    assert all(re.fullmatch(r"entry-[0-9a-f]{16}", name) for name in names)
    assert len(set(names)) == len(names)
