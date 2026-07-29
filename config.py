"""
Shared configuration for BlueWhisper's Bluetooth RFCOMM service.

The server and client must agree on the same service UUID - it's how the
client identifies which service on the target device to connect to when
several Bluetooth services might be running there.
"""

SERVICE_NAME = "BlueWhisper"

# Fixed UUID for this project's SPP (serial) service. Do not change this
# once server and client are both using it, or they won't find each other.
SERVICE_UUID = "f3fc42eb-a20d-4a89-80fd-e302a26d050b"
