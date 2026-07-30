"""
BlueWhisper - Day 3: RFCOMM client with end-to-end encryption.

Same Bluetooth connection as Day 2, but immediately after connecting, both
sides perform an X25519 key exchange (see crypto_utils.py) and every message
from then on is encrypted with AES-256-GCM. See docs/ARCHITECTURE.md for the
full protocol design.

Requirements:
    pip install pybluez2 cryptography

Usage:
    python src/client.py <server_mac_address>

Example:
    python src/client.py AA:BB:CC:DD:EE:FF
"""

import sys
import threading

try:
    import bluetooth
except ImportError:
    print("Missing dependency. Install it with:\n    pip install pybluez2")
    sys.exit(1)

from cryptography.exceptions import InvalidTag

from config import SERVICE_UUID
from crypto_utils import perform_handshake, send_encrypted, recv_encrypted


def listen_for_messages(sock, key):
    """Read, decrypt, and print incoming messages until the connection closes."""
    while True:
        try:
            plaintext = recv_encrypted(sock, key)
        except ConnectionError:
            print("\n[Connection closed by peer]")
            break
        except InvalidTag:
            print("\n[Received a message that failed verification - discarded]")
            continue
        print(f"\rPeer: {plaintext}\nYou: ", end="", flush=True)


def start_client(server_mac: str):
    print(f"Looking up BlueWhisper service on {server_mac}...")
    matches = bluetooth.find_service(uuid=SERVICE_UUID, address=server_mac)

    if not matches:
        print("No matching service found. Make sure:")
        print("  - src/server.py is running on the target device")
        print("  - the MAC address is correct (run src/discovery.py to check)")
        print("  - both devices are paired/discoverable and in range")
        sys.exit(1)

    service = matches[0]
    port = service["port"]
    host = service["host"]

    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.connect((host, port))
    print(f"Connected to {host}")

    print("Performing key exchange...")
    key = perform_handshake(sock)
    print("Secure channel established - messages are now end-to-end encrypted.")
    print("Type a message and press Enter to send. Type /quit to exit.\n")

    listener = threading.Thread(target=listen_for_messages, args=(sock, key), daemon=True)
    listener.start()

    try:
        while True:
            message = input("You: ")
            if message.strip().lower() in ("/quit", "/exit"):
                break
            if message:
                send_encrypted(sock, key, message)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        print("\nClosing connection...")
        sock.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python src/client.py <server_mac_address>")
        sys.exit(1)
    start_client(sys.argv[1])
