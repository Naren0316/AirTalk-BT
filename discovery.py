"""
BlueWhisper - Day 1: Bluetooth device discovery.

Scans for nearby discoverable Bluetooth devices and prints their name and
MAC address. The MAC address of the device you want to chat with is what
Day 2's connection code will use to open an RFCOMM socket.

Requirements:
    pip install pybluez2

Usage:
    python src/discovery.py
"""

import sys

try:
    import bluetooth
except ImportError:
    print("Missing dependency. Install it with:\n    pip install pybluez2")
    sys.exit(1)


def discover_devices(duration: int = 8):
    """
    Scan for nearby discoverable Bluetooth devices.

    Args:
        duration: how many seconds to scan for. Longer scans find more
            devices but take proportionally longer.

    Returns:
        A list of (mac_address, device_name) tuples.
    """
    print("Scanning for nearby Bluetooth devices...")
    print(f"(this takes about {duration} seconds - make sure the other "
          f"device has Bluetooth on and is set to discoverable)\n")

    try:
        nearby_devices = bluetooth.discover_devices(
            duration=duration,
            lookup_names=True,
            flush_cache=True,
            lookup_class=False,
        )
    except OSError as e:
        print(f"Could not scan for devices: {e}")
        print("Check that Bluetooth is turned on for this machine.")
        return []

    if not nearby_devices:
        print("No devices found.")
        print("- Make sure Bluetooth is enabled on both devices")
        print("- Make sure the other device is set to 'discoverable'")
        print("- Try moving the devices closer together and re-running")
        return []

    print(f"Found {len(nearby_devices)} device(s):\n")
    for addr, name in nearby_devices:
        print(f"  {name!r:25s}  {addr}")

    return nearby_devices


if __name__ == "__main__":
    discover_devices()
