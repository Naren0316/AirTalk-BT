"""
BlueWhisper - Day 3: RFCOMM server with end-to-end encryption.

Same Bluetooth connection as Day 2, but immediately after connecting, both
sides perform an X25519 key exchange (see crypto_utils.py) and every message
from then on is encrypted with AES-256-GCM. See docs/ARCHITECTURE.md for the
full protocol design.

Requirements:
    pip install pybluez2 cryptography

Usage:
    python src/server.py

Then, on the other device, run:
    python src/client.py <this device's MAC address>
"""

import sys
import threading

try:
    import bluetooth
except ImportError:
    print("Missing dependency. Install it with:\n    pip install pybluez2")
    sys.exit(1)

from cryptography.exceptions import InvalidTag

from config import SERVICE_NAME, SERVICE_UUID
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


def start_server():
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

    print(f"BlueWhisper server started on RFCOMM channel {port}.")
    print("Make sure this device is set to 'discoverable', then run")
    print("src/client.py from the other device, pointed at this device's MAC address.")
    print("\nWaiting for a connection...\n")

    client_sock, client_info = server_sock.accept()
    print(f"Connected to {client_info[0]}")

    print("Performing key exchange...")
    key = perform_handshake(client_sock)
    print("Secure channel established - messages are now end-to-end encrypted.")
    print("Type a message and press Enter to send. Type /quit to exit.\n")

    listener = threading.Thread(target=listen_for_messages, args=(client_sock, key), daemon=True)
    listener.start()

    try:
        while True:
            message = input("You: ")
            if message.strip().lower() in ("/quit", "/exit"):
                break
            if message:
                send_encrypted(client_sock, key, message)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        print("\nClosing connection...")
        client_sock.close()
        server_sock.close()


if __name__ == "__main__":
    start_server()
