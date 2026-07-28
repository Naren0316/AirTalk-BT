# BlueWhisper

A fully offline, peer-to-peer chat tool that sends **end-to-end encrypted** text messages directly over **Bluetooth** — no SIM card, no Wi-Fi, no internet, no server in the middle.

Two devices with Bluetooth radios pair directly and exchange messages over a Bluetooth serial (RFCOMM) socket. Every message is encrypted on the sender's device and only decrypted on the recipient's device.

## Status

🚧 Day 1 of 5 — project scaffolding + device discovery. See [Roadmap](#roadmap) below.

## Why

Regular chat apps need a SIM, Wi-Fi, or a server. BlueWhisper needs none of that — only two Bluetooth radios in range of each other (roughly up to ~10 m for Class 2 Bluetooth). Useful for:
- Messaging with zero connectivity (flights, remote areas, outages)
- Learning how offline transport + real E2E encryption is built from scratch
- A portfolio project that demonstrates both networking and applied cryptography

## How it works (high level)

```
Device A                                   Device B
--------                                   --------
1. Discover nearby Bluetooth devices  <-->  (discoverable mode)
2. Pair / connect via RFCOMM socket   <-->  RFCOMM server socket
3. Exchange public keys (ECDH)        <-->  Exchange public keys (ECDH)
4. Derive shared AES key (HKDF)             Derive shared AES key (HKDF)
5. Encrypt message (AES-256-GCM)      -->   Decrypt + verify message
```

Full protocol design lives in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Roadmap

| Day | Milestone | Status |
|-----|-----------|--------|
| 1 | Repo setup, architecture design, Bluetooth device discovery | ✅ Done |
| 2 | RFCOMM connection — server + client exchange plaintext messages | ⬜ Pending |
| 3 | End-to-end encryption layer — X25519 key exchange + AES-256-GCM | ⬜ Pending |
| 4 | Chat interface (CLI) — message framing, contacts, reconnection handling | ⬜ Pending |
| 5 | Testing, edge cases, docs, demo, final polish | ⬜ Pending |

## Requirements

- Python 3.9+
- A Bluetooth radio on the host machine
- Two devices to test between (two laptops, or a laptop + another PyBluez2-capable machine)

## Installation

```bash
git clone https://github.com/Naren0316/BlueWhisper.git
cd BlueWhisper
pip install -r requirements.txt
```

> **Linux users:** you'll also need the system Bluetooth dev headers first:
> `sudo apt-get install bluetooth libbluetooth-dev`

## Usage (Day 1)

Scan for nearby discoverable Bluetooth devices:

```bash
python src/discovery.py
```

This prints the name and MAC address of every discoverable device nearby — the MAC address is what Day 2's connection code will target.

## Project structure

```
BlueWhisper/
├── README.md
├── LICENSE
├── requirements.txt
├── docs/
│   └── ARCHITECTURE.md      # protocol + encryption design
└── src/
    └── discovery.py         # Day 1: nearby device scanner
```

## License

MIT — see [LICENSE](LICENSE).
