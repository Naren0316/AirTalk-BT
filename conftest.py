"""
Shared pytest setup for the BlueWhisper test suite.

Adds src/ to sys.path (the project doesn't package src/ as an installable
module - these tests import its files directly) and provides fixtures that
isolate contacts.py and session.py from the real contacts.json/logs/ on
disk, so running tests never touches your actual saved contacts or chat
history.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import pytest


@pytest.fixture
def isolated_contacts_file(tmp_path, monkeypatch):
    """Point contacts.py at a throwaway file for the duration of one test."""
    import contacts

    monkeypatch.setattr(contacts, "CONTACTS_FILE", str(tmp_path / "contacts.json"))


@pytest.fixture
def isolated_log_dir(tmp_path, monkeypatch):
    """Point session.py's chat logs at a throwaway directory for one test."""
    import session

    monkeypatch.setattr(session, "LOG_DIR", str(tmp_path / "logs"))
