"""
BlueWhisper - Day 4: main chat application.

The everyday way to run BlueWhisper - one menu that wraps discovery,
contacts, the Bluetooth connection, the encryption handshake, and the chat
loop, instead of running discovery.py / server.py / client.py by hand each
time. (server.py and client.py from Days 2-3 still work standalone too.)

Requirements:
    pip install pybluez2 cryptography

Usage:
    python src/chat.py
"""

import sys
import time

try:
    import bluetooth
except ImportError:
    print("Missing dependency. Install it with:\n    pip install pybluez2")
    sys.exit(1)

import contacts
from config import SERVICE_NAME, SERVICE_UUID
from crypto_utils import perform_handshake
from discovery import discover_devices
from session import run_chat_session

MAX_CONNECT_RETRIES = 3
RETRY_DELAY_SECONDS = 3


def _label_for_mac(mac_address: str) -> str:
    """Return a saved contact's name for this MAC address, or the MAC itself."""
    for name, saved_mac in contacts.list_contacts().items():
        if saved_mac == mac_address:
            return name
    return mac_address


def host_chat():
    """Wait for someone to connect, then chat with them."""
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", bluetooth.PORT_ANY))
    server_sock.listen(1)
    port = server_sock.getsockname()[1]

    bluetooth.advertise_service(
        server_sock,
        SERVICE_NAME,
        service_id=SERVICE_UUID,
        service_classes=[SERVICE_UUID, bluetooth.SERIAL_PORT_CLASS],
        profiles=[bluetooth.SERIAL_PORT_PROFILE],
    )

    print(f"Waiting for a connection on RFCOMM channel {port}...")
    print("Make sure this device is set to 'discoverable'. (Ctrl+C to cancel)\n")

    try:
        client_sock, client_info = server_sock.accept()
    except KeyboardInterrupt:
        print("\nCancelled.")
        server_sock.close()
        return
    peer_mac = client_info[0]
    peer_label = _label_for_mac(peer_mac)
    print(f"Connected to {peer_label} ({peer_mac})")

    print("Performing key exchange...")
    try:
        key = perform_handshake(client_sock)
    except (ConnectionError, OSError, ValueError) as e:
        print(f"Key exchange failed: {e}")
        client_sock.close()
        server_sock.close()
        return
    print("Secure channel established.\n")

    run_chat_session(client_sock, key, peer_label)
    server_sock.close()


def connect_to_contact():
    """Pick a saved contact and connect to them, retrying on failure."""
    saved = contacts.list_contacts()
    if not saved:
        print("No saved contacts yet. Add one from the main menu first.")
        return

    names = list(saved.keys())
    print("\nSaved contacts:")
    for i, name in enumerate(names, start=1):
        print(f"  {i}. {name} ({saved[name]})")

    choice = input("\nWhich contact do you want to message? (number): ").strip()
    if not choice.isdigit() or not (1 <= int(choice) <= len(names)):
        print("Invalid choice.")
        return

    name = names[int(choice) - 1]
    mac_address = saved[name]

    for attempt in range(1, MAX_CONNECT_RETRIES + 1):
        print(f"\nConnecting to {name} ({mac_address})... (attempt {attempt}/{MAX_CONNECT_RETRIES})")
        try:
            matches = bluetooth.find_service(uuid=SERVICE_UUID, address=mac_address)
            if not matches:
                raise ConnectionError("BlueWhisper doesn't seem to be running on that device right now")

            service = matches[0]
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            sock.connect((service["host"], service["port"]))

            print("Performing key exchange...")
            key = perform_handshake(sock)
            print("Secure channel established.\n")

            run_chat_session(sock, key, name)
            return
        except KeyboardInterrupt:
            print("\nCancelled.")
            return
        except (bluetooth.BluetoothError, OSError, ConnectionError, ValueError) as e:
            print(f"Couldn't connect: {e}")
            if attempt < MAX_CONNECT_RETRIES:
                print(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                time.sleep(RETRY_DELAY_SECONDS)

    print(
        f"\nGave up after {MAX_CONNECT_RETRIES} attempts. Make sure {name}'s "
        f"device has Bluetooth on and BlueWhisper running in host mode."
    )


def add_new_contact():
    """Scan for nearby devices and save one as a named contact."""
    devices = discover_devices()
    if not devices:
        return

    choice = input("\nWhich device do you want to save? (number, or blank to cancel): ").strip()
    if not choice:
        return
    if not choice.isdigit() or not (1 <= int(choice) <= len(devices)):
        print("Invalid choice.")
        return

    mac_address, discovered_name = devices[int(choice) - 1]
    name = input(f"Save '{discovered_name}' ({mac_address}) as: ").strip() or discovered_name
    contacts.add_contact(name, mac_address)
    print(f"Saved {name} ({mac_address}).")


def main_menu():
    while True:
        print("\n=== BlueWhisper ===")
        print("1. Host a chat (wait for someone to connect to you)")
        print("2. Connect to a saved contact")
        print("3. Add a new contact (scan for nearby devices)")
        print("4. Exit")
        try:
            choice = input("\nChoose an option: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if choice == "1":
            host_chat()
        elif choice == "2":
            connect_to_contact()
        elif choice == "3":
            add_new_contact()
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice, try again.")


if __name__ == "__main__":
    main_menu()
