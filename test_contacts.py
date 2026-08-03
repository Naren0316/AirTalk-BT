"""
Tests for contacts.py. Every test uses the isolated_contacts_file fixture
(see conftest.py) so they never touch the real contacts.json on whatever
machine runs the suite.
"""

import contacts


def test_starts_empty(isolated_contacts_file):
    assert contacts.list_contacts() == {}


def test_add_and_get_contact(isolated_contacts_file):
    contacts.add_contact("Rohan", "AA:BB:CC:DD:EE:01")
    assert contacts.get_contact("Rohan") == "AA:BB:CC:DD:EE:01"


def test_get_unknown_contact_returns_none(isolated_contacts_file):
    assert contacts.get_contact("Nobody") is None


def test_list_contacts_returns_all(isolated_contacts_file):
    contacts.add_contact("Rohan", "AA:BB:CC:DD:EE:01")
    contacts.add_contact("Priya", "AA:BB:CC:DD:EE:02")
    assert contacts.list_contacts() == {
        "Rohan": "AA:BB:CC:DD:EE:01",
        "Priya": "AA:BB:CC:DD:EE:02",
    }


def test_adding_same_name_overwrites(isolated_contacts_file):
    contacts.add_contact("Rohan", "AA:BB:CC:DD:EE:01")
    contacts.add_contact("Rohan", "AA:BB:CC:DD:EE:99")
    assert contacts.get_contact("Rohan") == "AA:BB:CC:DD:EE:99"
    assert len(contacts.list_contacts()) == 1


def test_remove_contact(isolated_contacts_file):
    contacts.add_contact("Rohan", "AA:BB:CC:DD:EE:01")
    assert contacts.remove_contact("Rohan") is True
    assert contacts.get_contact("Rohan") is None


def test_remove_unknown_contact_returns_false(isolated_contacts_file):
    assert contacts.remove_contact("Nobody") is False


def test_survives_corrupted_contacts_file(isolated_contacts_file):
    with open(contacts.CONTACTS_FILE, "w", encoding="utf-8") as f:
        f.write("not valid json {{{")

    # Should treat a corrupted file as empty rather than crash
    assert contacts.list_contacts() == {}
