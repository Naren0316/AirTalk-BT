"""
Tests for the parts of session.py that don't need a real socket connection:
timestamp formatting, log file path generation, and writing to the log.
The interactive chat loop itself (run_chat_session) is exercised manually
per docs/DEMO.md, since it drives real input()/socket I/O.
"""

import os
import re

import session


def test_timestamp_format():
    ts = session._timestamp()
    assert re.match(r"^\d{2}:\d{2}:\d{2}$", ts)


def test_log_path_creates_log_dir(isolated_log_dir):
    session._log_path("Rohan")
    assert os.path.isdir(session.LOG_DIR)


def test_log_path_includes_peer_label(isolated_log_dir):
    path = session._log_path("Rohan")
    assert "Rohan" in os.path.basename(path)


def test_log_path_sanitizes_unsafe_characters(isolated_log_dir):
    # A MAC address (used as peer_label when there's no saved contact name)
    # contains colons, which aren't safe in filenames on every OS.
    path = session._log_path("AA:BB:CC:DD:EE:FF")
    filename = os.path.basename(path)
    assert ":" not in filename


def test_append_log_writes_lines(isolated_log_dir):
    path = session._log_path("Rohan")
    session._append_log(path, "[12:00:00] You: hello")
    session._append_log(path, "[12:00:05] Peer: hi there")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "[12:00:00] You: hello" in content
    assert "[12:00:05] Peer: hi there" in content
