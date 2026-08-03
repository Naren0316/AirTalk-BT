# BlueWhisper

A fully offline, peer-to-peer chat tool that sends **end-to-end encrypted** text messages directly over **Bluetooth** — no SIM card, no Wi-Fi, no internet, no server in the middle.

Two devices with Bluetooth radios pair directly and exchange messages over a Bluetooth serial (RFCOMM) socket. Every message is encrypted on the sender's device and only decrypted on the recipient's device.

## Status

✅ All 5 days complete — see [Roadmap](#roadmap) for what each day added.

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
| 2 | RFCOMM connection — server + client exchange plaintext messages | ✅ Done |
| 3 | End-to-end encryption layer — X25519 key exchange + AES-256-GCM | ✅ Done |
| 4 | Chat interface (CLI) — message framing, contacts, reconnection handling | ✅ Done |
| 5 | Testing, edge cases, docs, demo, final polish | ✅ Done |

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

To also run the test suite, additionally install `requirements-dev.txt` (see [Testing](#testing) below).

## Usage

The easiest way to run BlueWhisper is `chat.py` — one menu that handles discovery, contacts, connecting, and the encrypted chat loop:

```bash
python src/chat.py
```

```
=== BlueWhisper ===
1. Host a chat (wait for someone to connect to you)
2. Connect to a saved contact
3. Add a new contact (scan for nearby devices)
4. Exit
```

**First time messaging someone:** on one device, choose **1** to host. On the other, choose **3** to scan for nearby devices and save the host as a named contact, then choose **2** to connect to them.

**After that:** just choose **2** and pick their name — no need to re-scan every time.

Once connected, both sides automatically run an X25519 key exchange ("Performing key exchange..." → "Secure channel established"), then every message is encrypted with AES-256-GCM before it's sent. Type `/quit` to end the session. Each conversation is timestamped and saved to a local log file under `logs/` (git-ignored — this is local-only data, never transmitted).

If a connection attempt fails, `chat.py` retries automatically (3 attempts, a few seconds apart) before giving up with a clear message — useful if the other device's Bluetooth briefly drops or hasn't started BlueWhisper yet.

### Lower-level scripts (Days 1-3)

These still work standalone and are useful for understanding each layer individually, or for quick manual testing without the contacts/menu system:

```bash
python src/discovery.py          # scan for nearby devices and their MAC addresses
python src/server.py             # host mode: wait for one connection, encrypted chat
python src/client.py AA:BB:CC:DD:EE:FF   # connect mode: connect by MAC address
```

## Testing

The encryption layer, contact book, and chat logging are covered by an automated test suite that runs without any Bluetooth hardware — `crypto_utils.py`'s tests use a local loopback socket pair (`socket.socketpair()`), which has the identical `send()`/`recv()` interface a real Bluetooth socket has.

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

23 tests, covering:
- the handshake produces matching keys on both sides, and a fresh key every session
- messages round-trip correctly (including empty strings and Unicode)
- tampered ciphertext and a wrong decryption key are both rejected
- a disconnect mid-read raises a clean error instead of hanging
- a corrupted/oversized length header is rejected before it can trigger a huge allocation
- a malformed handshake message is rejected cleanly
- the contact book's add/get/list/overwrite/remove behavior, including recovering from a corrupted `contacts.json`
- chat log file naming and writing, including sanitizing MAC-address characters that aren't filename-safe

What's **not** covered by automated tests (needs real hardware, see [docs/DEMO.md](docs/DEMO.md) for a manual walkthrough): actual Bluetooth device discovery, RFCOMM connection/acceptance, and the interactive chat loop's I/O.

## Known limitations

Worth being upfront about, especially if this comes up in a review:

- **Direct connections only** — no multi-hop mesh relay. Both devices need to be within Bluetooth range of each other (see [Architecture](docs/ARCHITECTURE.md#5-why-not-ble--a-mesh-network) for why).
- **No identity verification beyond Bluetooth pairing** — the encryption guarantees the *content* wasn't read or tampered with in transit, but doesn't independently confirm you're talking to the right person, beyond having connected to the right MAC address. Apps like Signal add a manual safety-number comparison for this; BlueWhisper doesn't yet.
- **One connection at a time** — the server accepts a single client per run; no group chats.
- **Chat logs are stored as plaintext locally** — readable to anyone with access to the device's filesystem, since they're decrypted for you to read. They're never transmitted anywhere.
- **PyBluez2's BLE peripheral support is Linux-only** — this project deliberately uses Bluetooth Classic (RFCOMM) instead, specifically to avoid that limitation (see the architecture doc for the reasoning).

## Project structure

```
BlueWhisper/
├── README.md
├── LICENSE
├── requirements.txt
├── requirements-dev.txt     # Day 5: pytest, for running tests/
├── docs/
│   ├── ARCHITECTURE.md      # protocol + encryption design
│   └── DEMO.md              # Day 5: script for recording a demo
├── tests/                   # Day 5: automated test suite (23 tests)
│   ├── conftest.py
│   ├── test_crypto_utils.py
│   ├── test_contacts.py
│   └── test_session.py
└── src/
    ├── discovery.py         # Day 1: nearby device scanner
    ├── config.py            # Day 2: shared service name/UUID
    ├── server.py            # Day 2-3: RFCOMM server + encrypted chat (standalone)
    ├── client.py            # Day 2-3: RFCOMM client + encrypted chat (standalone)
    ├── crypto_utils.py      # Day 3: X25519 handshake, AES-256-GCM, framing
    ├── contacts.py          # Day 4: local contact book (contacts.json)
    ├── session.py           # Day 4: shared chat loop - timestamps + logging
    └── chat.py              # Day 4: main menu-driven app (recommended entry point)
```

## License

MIT — see [LICENSE](LICENSE).
