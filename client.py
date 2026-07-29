"""
BlueWhisper - Day 2: RFCOMM client.

Connects to a BlueWhisper server running on another device (find its MAC
address first with src/discovery.py) and exchanges plain text messages.

Encryption is NOT implemented yet - that's Day 3. Everything sent today is
plaintext, for testing the connection itself.

Requirements:
    pip install pybluez2

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

from config import SERVICE_UUID


def listen_for_messages(sock):
    """Read incoming messages from the socket and print them, until it closes."""
    while True:
        try:
            data = sock.recv(4096)
        except OSError:
            print("\n[Connection closed]")
            break
        if not data:
            print("\n[Connection closed by peer]")
            break
        print(f"\rPeer: {data.decode('utf-8', errors='replace')}\nYou: ", end="", flush=True)


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
    print("Type a message and press Enter to send. Type /quit to exit.\n")

    listener = threading.Thread(target=listen_for_messages, args=(sock,), daemon=True)
    listener.start()

    try:
        while True:
            message = input("You: ")
            if message.strip().lower() in ("/quit", "/exit"):
                break
            if message:
                sock.send(message.encode("utf-8"))
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
