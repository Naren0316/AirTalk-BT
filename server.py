"""
BlueWhisper - Day 2: RFCOMM server.

Advertises a Bluetooth Serial Port Profile (SPP) service and waits for a
client (src/client.py, running on the other device) to connect. Once
connected, both sides can send and receive plain text messages at the same
time.

Encryption is NOT implemented yet - that's Day 3. Everything sent today is
plaintext, for testing the connection itself.

Requirements:
    pip install pybluez2

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

from config import SERVICE_NAME, SERVICE_UUID


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
    print("Type a message and press Enter to send. Type /quit to exit.\n")

    listener = threading.Thread(target=listen_for_messages, args=(client_sock,), daemon=True)
    listener.start()

    try:
        while True:
            message = input("You: ")
            if message.strip().lower() in ("/quit", "/exit"):
                break
            if message:
                client_sock.send(message.encode("utf-8"))
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        print("\nClosing connection...")
        client_sock.close()
        server_sock.close()


if __name__ == "__main__":
    start_server()
