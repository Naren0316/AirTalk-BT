"""
BlueWhisper - Day 4: contact book.

Stores known devices (a friendly name -> Bluetooth MAC address) in a local
JSON file, so you don't need to re-run discovery.py every time you want to
message someone you've already found before.

contacts.json lives in the project root and is git-ignored - it's local
device data specific to your machine, not something to commit.
"""

import json
import os

CONTACTS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "contacts.json"
)


def _load() -> dict:
    if not os.path.exists(CONTACTS_FILE):
        return {}
    with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save(contacts: dict):
    with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
        json.dump(contacts, f, indent=2)


def list_contacts() -> dict:
    """Return {name: mac_address} for every saved contact."""
    return _load()


def add_contact(name: str, mac_address: str):
    """Save (or overwrite) a contact by name."""
    contacts = _load()
    contacts[name] = mac_address
    _save(contacts)


def get_contact(name: str):
    """Return the MAC address saved for this contact name, or None."""
    return _load().get(name)


def remove_contact(name: str) -> bool:
    """Remove a saved contact. Returns True if it existed, False otherwise."""
    contacts = _load()
    if name in contacts:
        del contacts[name]
        _save(contacts)
        return True
    return False
